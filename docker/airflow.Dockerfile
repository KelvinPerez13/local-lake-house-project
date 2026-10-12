FROM apache/airflow:2.10.5-python3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps && rm -rf /var/lib/apt/lists/* && mkdir -p /opt/airflow/state && chown airflow:0 /opt/airflow/state
USER airflow
RUN pip install --no-cache-dir apache-airflow==2.10.5 pyspark==3.5.4 boto3==1.36.3 'psycopg[binary]==3.2.5' --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt
RUN JARS=$(python -c "import pyspark,os; print(os.path.join(os.path.dirname(pyspark.__file__),'jars'))") && \
    curl -fSL --retry 3 https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.8.1/iceberg-spark-runtime-3.5_2.12-1.8.1.jar -o "$JARS/iceberg-spark-runtime.jar" && \
    curl -fSL --retry 3 https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-aws-bundle/1.8.1/iceberg-aws-bundle-1.8.1.jar -o "$JARS/iceberg-aws-bundle.jar"
WORKDIR /app
COPY pipelines /app/pipelines
COPY dags /app/dags
ENV PYTHONPATH=/app SPARK_LOCAL_IP=127.0.0.1
