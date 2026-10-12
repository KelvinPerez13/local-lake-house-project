import os
from pyspark.sql import SparkSession
from pipelines.common import wait_catalog

def get_spark():
    wait_catalog()
    config = {
        'spark.sql.extensions': 'org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions',
        'spark.sql.catalog.lab': 'org.apache.iceberg.spark.SparkCatalog',
        'spark.sql.catalog.lab.type': 'rest',
        'spark.sql.catalog.lab.uri': os.environ['CATALOG_URI'],
        'spark.sql.catalog.lab.warehouse': 's3://warehouse/iceberg',
        'spark.sql.catalog.lab.io-impl': 'org.apache.iceberg.aws.s3.S3FileIO',
        'spark.sql.catalog.lab.s3.endpoint': os.environ['S3_ENDPOINT'],
        'spark.sql.catalog.lab.s3.path-style-access': 'true',
        'spark.sql.catalog.lab.rest.auth.type': 'none',
        'spark.sql.shuffle.partitions': '2',
        'spark.sql.session.timeZone': 'UTC',
        'spark.ui.enabled': 'false',
    }
    builder = SparkSession.builder.master('local[2]').appName('lakehouse-lab')
    for key, value in config.items():
        builder = builder.config(key, value)
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel('WARN')
    return spark
