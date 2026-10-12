"""Bronze JSON -> silver validada -> gold; refresh completo sem duplicação."""
import json
import tempfile
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, LongType, StringType
from pipelines.common import s3, bucket
from pipelines.spark_session import get_spark

SCHEMAS = {
    'customers': StructType([StructField('id', LongType()), StructField('name', StringType()), StructField('country', StringType())]),
    'orders': StructType([StructField('id', LongType()), StructField('customer_id', LongType()), StructField('amount', StringType()), StructField('status', StringType()), StructField('ordered_at', StringType())]),
}

def replace(df, table):
    df.writeTo(table).using('iceberg').tableProperty('format-version', '2').createOrReplace()

def main():
    client = s3()
    manifest = json.loads(client.get_object(Bucket=bucket(), Key='bronze/latest.json')['Body'].read())
    spark = get_spark()
    try:
        for ns in ('silver', 'gold'):
            spark.sql(f'CREATE NAMESPACE IF NOT EXISTS lab.{ns}')
        with tempfile.TemporaryDirectory() as tmp:
            frames = {}
            for table, schema in SCHEMAS.items():
                path = Path(tmp) / f'{table}.jsonl'
                client.download_file(bucket(), manifest['tables'][table]['key'], str(path))
                df = spark.read.schema(schema).option('mode', 'FAILFAST').json(str(path)).cache()
                if df.count() != manifest['tables'][table]['count']:
                    raise ValueError('Contagem bronze inconsistente')
                if df.filter('id IS NULL').count() or df.select('id').distinct().count() != df.count():
                    raise ValueError(f'Chave inválida em {table}')
                frames[table] = df
            customers = frames['customers']
            orders = (frames['orders'].withColumn('amount', F.col('amount').cast('decimal(12,2)'))
                      .withColumn('ordered_at', F.to_timestamp('ordered_at')))
            invalid = orders.filter("amount IS NULL OR amount < 0 OR ordered_at IS NULL OR status IS NULL OR status NOT IN ('paid','pending','cancelled')")
            if invalid.count() or orders.join(customers, orders.customer_id == customers.id, 'left_anti').count():
                raise ValueError('Pedidos inválidos; nenhuma tabela foi publicada')
            replace(customers, 'lab.silver.customers')
            replace(orders, 'lab.silver.orders')
            gold = (orders.filter("status = 'paid'").join(customers, orders.customer_id == customers.id)
                    .groupBy(F.to_date('ordered_at').alias('order_date'), 'country')
                    .agg(F.count('*').alias('order_count'), F.sum('amount').alias('revenue')))
            replace(gold, 'lab.gold.daily_revenue')
            gold.orderBy('order_date', 'country').show()
        print('Pipeline concluído:', manifest['run_id'])
    finally:
        spark.stop()

if __name__ == '__main__':
    main()
