$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    if (-not (Test-Path -LiteralPath '.env')) {
        throw 'Crie .env a partir de .env.example e ajuste os valores locais antes de executar.'
    }
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar serviços' }
    docker compose --profile jobs run --build --rm ingestion
    if ($LASTEXITCODE -ne 0) { throw 'Falha na ingestão' }
    docker compose --profile jobs run --build --rm spark
    if ($LASTEXITCODE -ne 0) { throw 'Falha na transformação' }
    docker compose --profile jobs run --rm spark python -m tests.smoke
    if ($LASTEXITCODE -ne 0) { throw 'Falha no smoke test' }
} finally {
    Pop-Location
}
