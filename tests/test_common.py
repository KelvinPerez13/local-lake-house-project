import json
from datetime import datetime, timezone
from decimal import Decimal
from pipelines.common import encode_rows

def test_ndjson_preserves_decimal_and_unicode():
    raw = encode_rows([{'amount': Decimal('12.30'), 'name': 'João'}, {'at': datetime(2025,1,1,tzinfo=timezone.utc)}])
    rows = [json.loads(line) for line in raw.splitlines()]
    assert rows[0] == {'amount': '12.30', 'name': 'João'}
    assert rows[1]['at'].startswith('2025-01-01')

def test_newlines_inside_text_do_not_split_records():
    raw = encode_rows([{'name': 'linha 1\nlinha 2', 'note': '"texto"'}])
    assert len(raw.splitlines()) == 1
    assert json.loads(raw)['name'] == 'linha 1\nlinha 2'
