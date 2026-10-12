import json
import os
import time
import urllib.request

TABLES = ('customers', 'orders')

def s3():
    import boto3
    from botocore.config import Config
    return boto3.client('s3', endpoint_url=os.environ['S3_ENDPOINT'],
                        config=Config(s3={'addressing_style': 'path'}))

def bucket():
    return os.environ.get('S3_BUCKET', 'warehouse')

def encode_rows(rows):
    return ('\n'.join(json.dumps(r, default=str, ensure_ascii=False) for r in rows) + '\n').encode()

def wait_catalog(timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(os.environ['CATALOG_URI'] + '/v1/config', timeout=5) as r:
                if r.status == 200:
                    return
        except (OSError, ValueError):
            time.sleep(2)
    raise TimeoutError('Catálogo REST indisponível; confira docker compose logs catalog')
