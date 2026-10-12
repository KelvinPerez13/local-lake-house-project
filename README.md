# Laboratório on-premises de engenharia de dados

Boilerplate didático AWS/Databricks-like, executado em Docker Compose.
Não depende de conta AWS. Não contém credenciais reais: todos os valores de
`.env.example` são exemplos locais, que devem ser trocados antes de iniciar.

## Arquitetura

```text
PostgreSQL (origem) -> Python/psycopg -> MinIO bronze JSONL
                                          |
                                    PySpark local[2]
                                          |
                         Iceberg silver -> Iceberg gold
                                 |              |
                         REST catálogo + MinIO arquivos
                                 |              |
                              Jupyter / Trino opcional
Airflow opcional: agenda ingestão -> transformação
```

| Papel | Serviço | Analogia aproximada |
|---|---|---|
| Origem relacional | PostgreSQL 16.6 | RDS PostgreSQL |
| Object storage | MinIO, release 2025-02-07 | S3 |
| Processamento | PySpark 3.5.5, Java 17, Scala 2.12 | EMR / compute Databricks |
| Formato de tabela | Iceberg 1.8.1 | Lakehouse aberto |
| Catálogo | Iceberg REST fixture 1.8.1 + JDBC SQLite persistido | parte do papel de Glue |
| Notebooks | JupyterLab 4.3.5 | exploração em notebooks |
| SQL opcional | Trino 471 | Athena |
| Orquestração opcional | Airflow 2.10.5 | MWAA |

As analogias são de função: não reproduzem IAM, Unity Catalog, Delta Lake,
autoscaling ou funcionalidades exclusivas das plataformas comerciais.

## Pré-requisitos

- Docker Engine/Desktop com containers Linux e Docker Compose v2.24+.
- Windows: Docker Desktop com WSL2. Execute os comandos na pasta extraída.
- Recomendado: 4 CPUs, 8 GB RAM disponíveis para Docker (12–16 GB com opcionais),
  15 GB livres. Primeiro build precisa de internet para imagens, pip, Maven e Go.
  MinIO é compilado da release fixa com Go 1.23.6, pois as imagens públicas
  consultadas ficaram indisponíveis. Esse build inicial pode levar vários minutos.
- Portas locais: 5433, 9000, 9001, 8181, 8888; opcionais 8080/8081.
- Imagens e dependências diretas têm versões fixas; dependências transitivas de pip
  e tags Docker não equivalem a um lock criptográfico integral.

## Quickstart

1. Crie o arquivo de configuração:

```powershell
# PowerShell
Copy-Item .env.example .env
```

```sh
# Linux/macOS
cp .env.example .env
```

Edite `.env` e troque os três segredos de demonstração. Não use credenciais AWS.
O bucket `warehouse` e os nomes dos serviços são fixos neste exemplo.

2. Suba os serviços principais:

```sh
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

`storage-init` terminar com código 0 é esperado. PostgreSQL carrega o SQL somente
na primeira criação do volume. O catálogo preserva registros em SQLite e MinIO
preserva dados em outro volume; ambos precisam ser mantidos juntos.

3. Execute as etapas em sequência (aguarde cada comando terminar):

```sh
docker compose --profile jobs run --build --rm ingestion
docker compose --profile jobs run --build --rm spark
docker compose --profile jobs run --rm ingestion python -m pytest -q
docker compose --profile jobs run --rm spark python -m tests.smoke
```

Resultado esperado: 3 clientes, 5 pedidos silver, gold BR=150.00 (2 pedidos) e
PT=75.50 (1 pedido). Pending/cancelled permanecem em silver e não entram na receita.
Para provar reexecução, execute ingestão, transformação e smoke novamente:
as contagens ficam iguais e Iceberg ganha novos snapshots.

Atalho após configurar `.env`: `./scripts/demo.ps1` no PowerShell ou
`sh scripts/demo.sh` no Linux/macOS. Ambos param ao primeiro erro.

4. Abra Jupyter em http://localhost:8888 e use o token de `.env`.
Abra `01-explorar.ipynb`. Console MinIO: http://localhost:9001, com os valores
locais de `.env`; navegue no bucket `warehouse`.

## Profiles opcionais

Trino:

```sh
docker compose --profile trino up -d trino
docker compose exec trino trino --execute "SELECT * FROM iceberg.gold.daily_revenue ORDER BY order_date, country"
```

Airflow: standalone com SequentialExecutor e SQLite, somente para estudo.
O container inclui PySpark 3.5.4 e boto3 1.36.3, conforme as constraints oficiais
do Airflow (compatíveis com o mesmo runtime Iceberg Spark 3.5); não usa socket Docker nem executa
containers de dentro do scheduler. O DAG executa o mesmo código do CLI.

```sh
docker compose --profile airflow up -d --build airflow
docker compose logs airflow
docker compose exec airflow cat /opt/airflow/standalone_admin_password.txt
```

Abra http://localhost:8080, usuário `admin`, senha gerada pelo Airflow; habilite e
dispare `lakehouse_demo`. A senha não está no ZIP. Metadata DB, logs e o arquivo
de senha gerada são preservados no volume Airflow.
Não rode DAG e CLI simultaneamente: o exemplo usa `bronze/latest.json` compartilhado.

## Organização e contratos

```text
compose.yaml             serviços e profiles
docker/                  imagens de ingestão, Spark, catálogo, Airflow
requirements/            dependências Python diretas fixadas
pipelines/common.py      utilitários S3, serialização e espera do catálogo
pipelines/ingest.py      snapshot consistente PostgreSQL -> bronze
pipelines/transform.py   validação, casts, publicação silver/gold
pipelines/spark_session.py configuração comum Spark/Iceberg
sql/01-demo.sql          schema e dados de demonstração
notebooks/               exploração e snapshots
dags/                    DAG manual Airflow
trino/                   configuração Iceberg REST + S3 nativo
tests/                   unitários e smoke integrado
docs/VALIDATION.md       verificações realizadas na entrega
scripts/                 atalhos do pipeline para PowerShell e shell
```

Bronze: `s3://warehouse/bronze/<run_id>/<table>.jsonl`, imutável por execução,
com manifesto e ponteiro `latest.json` publicado após ambos os uploads.
Ingestão usa REPEATABLE READ: as duas tabelas pertencem ao mesmo snapshot PostgreSQL.
Valores monetários são strings JSON e DECIMAL(12,2) em silver. UTC em Spark.
Silver: `lab.silver.customers`, `lab.silver.orders`. Gold: `lab.gold.daily_revenue`.
Cada tabela Iceberg é substituída atomicamente com createOrReplace, sem duplicar
linhas em reexecuções. A transação não abrange as três tabelas: uma falha intermediária
pode deixar camadas de execuções diferentes; reexecute para convergir.

O download bronze para um diretório temporário local evita misturar dependências
S3A/Hadoop com S3FileIO; Spark usa S3FileIO para tabelas Iceberg. Esta estratégia
e a ingestão que carrega tabelas na memória são adequadas a datasets pequenos.
Para escala: extração paginada/CDC, arquivos Parquet, processamento distribuído,
watermarks, MERGE e manifestos específicos por execução em vez de latest compartilhado.

## Operação e troubleshooting

```sh
docker compose logs --tail 100 catalog minio postgres
docker compose --profile jobs run --rm spark python -m tests.smoke
docker compose down
```

`down` preserva volumes. Para zerar **todos os dados do laboratório**, incluindo
origem, catálogo, objetos e Airflow (irreversível):

```sh
docker compose --profile airflow --profile trino --profile jobs down -v
```

- Falha de porta: altere apenas a porta à esquerda do mapeamento Compose.
- `NoSuchKey bronze/latest.json`: execute ingestão antes da transformação.
- REST indisponível: confira logs; o cliente aguarda até 120 segundos.
- Senhas alteradas após criar volumes: PostgreSQL não aplica a nova senha
  automaticamente; altere no banco ou faça o reset destrutivo consciente.
- Erros de download: verifique proxy e acesso a Docker Hub, PyPI, Maven Central.
- A imagem Airflow usa constraints oficiais; ajustes de versões precisam respeitá-las.

## Limitações e segurança local

Este é um laboratório de nó único: não oferece HA, backup, TLS, controle de acesso
por tabela, isolamento multiusuário ou observabilidade completa. O REST fixture
é destinado a testes e exemplos, não um catálogo de produção. SQLite persistido
evita perda ao reiniciar; para produção escolha catálogo REST suportado e banco robusto.
MinIO e catálogo utilizam credenciais amplas locais. Portas publicadas escutam
somente 127.0.0.1. Não exponha a rede pública. Imagens escolhidas por compatibilidade,
não por serem as versões mais recentes; revise vulnerabilidades antes de outro uso.
Não há CDC, incremental, compactação nem limpeza automática de snapshots/bronze.

## Referências de compatibilidade

- https://iceberg.apache.org/spark-quickstart/
- https://iceberg.apache.org/docs/1.8.1/spark-configuration/
- https://iceberg.apache.org/docs/1.8.1/aws/
- https://github.com/apache/iceberg/tree/apache-iceberg-1.8.1/docker/iceberg-rest-fixture
- https://trino.io/docs/current/connector/iceberg.html
- https://airflow.apache.org/docs/apache-airflow/2.10.5/installation/installing-from-pypi.html
- MinIO (AGPLv3), código da release compilada: https://github.com/minio/minio/tree/RELEASE.2025-02-07T23-21-09Z
