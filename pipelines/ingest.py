"""Snapshot consistente; publica o manifesto somente depois dos dois uploads."""
import json
from datetime import datetime, timezone
from uuid import uuid4
import psycopg
from psycopg.rows import dict_row
from pipelines.common import TABLES, s3, bucket, encode_rows

def main():
    client = s3()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    manifest = {'run_id': run_id, 'tables': {}}
    with psycopg.connect('', row_factory=dict_row) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for table in TABLES:
            # Nomes são uma allowlist fixa, nunca uma entrada externa.
            rows = conn.execute(f'SELECT * FROM public.{table} ORDER BY id').fetchall()
            key = f'bronze/{run_id}/{table}.jsonl'
            client.put_object(Bucket=bucket(), Key=key, Body=encode_rows(rows), ContentType='application/x-ndjson')
            manifest['tables'][table] = {'key': key, 'count': len(rows)}
    body = json.dumps(manifest).encode()
    client.put_object(Bucket=bucket(), Key=f'bronze/{run_id}/manifest.json', Body=body)
    client.put_object(Bucket=bucket(), Key='bronze/latest.json', Body=body)
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
