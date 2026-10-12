FROM python:3.11.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/spark.txt
ARG ICEBERG_VERSION=1.8.1
RUN JARS=$(python -c "import pyspark,os; print(os.path.join(os.path.dirname(pyspark.__file__),'jars'))") && \
    curl -fSL --retry 3 https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar -o "$JARS/iceberg-spark-runtime.jar" && \
    curl -fSL --retry 3 https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar -o "$JARS/iceberg-aws-bundle.jar"
COPY pipelines /app/pipelines
COPY tests /app/tests
COPY notebooks /app/notebooks
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 SPARK_LOCAL_IP=127.0.0.1
