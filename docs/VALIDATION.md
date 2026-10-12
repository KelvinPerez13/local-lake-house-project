# Validação da entrega

Executada em 11/10/2026, Windows + Docker Desktop Linux Engine 29.8.0,
containers linux/amd64. Projeto Compose isolado: `codex_lakehouse_validation`.
Usados apenas os valores fictícios de `.env.example`.

| Verificação | Resultado |
|---|---|
| Compose com todos os profiles | Configuração válida |
| Build principal | PostgreSQL, MinIO compilado, catálogo REST, Python, PySpark e Jupyter prontos |
| Testes unitários | Serialização decimal/data/Unicode e campos com quebras de linha |
| Ingestão PostgreSQL -> bronze | 3 clientes e 5 pedidos, manifesto publicado |
| Bronze -> Iceberg silver/gold | Concluído; BR 150.00, PT 75.50 |
| Smoke integrado | Contagens, valores DECIMAL e snapshots verificados |
| Segunda ingestão e transformação | Mesmas contagens e valores; sem duplicação |
| Reinício do catálogo | Smoke passou novamente; registros preservados no SQLite |
| Jupyter /login | HTTP 200 |
| Catálogo /v1/config | HTTP 200 |
| Trino 471 | Consulta SQL retornou BR,2,150.00 e PT,1,75.50 |
| Build Airflow opcional | Concluído com constraints oficiais |
| Airflow /health | Metadatabase e scheduler healthy |
| Airflow dags test lakehouse_demo 2025-01-03 | Bronze e silver_gold SUCCESS; smoke posterior passou |

Os testes usaram o mesmo código e configuração entregues. A interface gráfica
do notebook não foi operada; foram verificados o servidor HTTP e o processamento
PySpark comum ao notebook. O DAG foi executado pelo comando `airflow dags test`,
sem aguardar um disparo agendado. O DAG é manual (`schedule=None`).

Os containers de validação foram encerrados após os testes; imagens, cache de
build e volumes locais de demonstração ficaram disponíveis no Docker.
O ZIP contém somente fontes, configuração e documentação, sem dados de volumes,
`.env`, credenciais geradas, imagens Docker ou arquivos intermediários.

Limites: validado em amd64 e um único host; não foram testados ARM64,
cluster distribuído, dados de grande volume, concorrência, falha durante commit,
restauração de backup ou uso em produção. Imagens externas e downloads ainda
dependem da disponibilidade futura dos registros, PyPI, GitHub, Go e Maven.

MinIO: os pulls da antiga imagem Docker Hub e do Quay retornaram acesso negado
durante a validação. A entrega compila a release fixa do repositório oficial,
com o `go.mod` e `go.sum` dessa release. O primeiro build custa mais tempo e disco.
