from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG('lakehouse_demo', start_date=datetime(2025, 1, 1), schedule=None,
         catchup=False, max_active_runs=1, tags=['lab']) as dag:
    ingest = BashOperator(task_id='bronze', bash_command='python -m pipelines.ingest')
    transform = BashOperator(task_id='silver_gold', bash_command='python -m pipelines.transform')
    ingest >> transform
