FROM apache/airflow:2.10.0-python3.12
# RUN pip install --no-cache-dir airflow-clickhouse-plugin==1.4.0
#RUN pip install --no-cache-dir airflow-clickhouse-plugin[common.sql]

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openjdk-17-jre-headless \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
# COPY log4j2.properties /opt/bitnami/spark/conf/log4j2.properties
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
