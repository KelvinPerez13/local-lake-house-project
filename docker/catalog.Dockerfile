FROM apache/iceberg-rest-fixture:1.8.1
USER root
RUN mkdir -p /catalog && chown iceberg:iceberg /catalog
USER iceberg
