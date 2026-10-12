from decimal import Decimal
from pipelines.spark_session import get_spark

spark = get_spark()
try:
    assert spark.table('lab.silver.customers').count() == 3
    assert spark.table('lab.silver.orders').count() == 5
    rows = spark.sql('SELECT country, order_count, revenue FROM lab.gold.daily_revenue ORDER BY country').collect()
    assert [(r.country, r.order_count, r.revenue) for r in rows] == [('BR',2,Decimal('150.00')),('PT',1,Decimal('75.50'))]
    assert spark.sql('SELECT * FROM lab.gold.daily_revenue.snapshots').count() >= 1
    print('SMOKE OK: contagens, valores monetários e snapshots Iceberg')
finally:
    spark.stop()
