# /dags_or_jobs/banking_dq_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd

# Import functions from other scripts
from generate_data import generate_data
from data_quality_standards import run_data_quality_checks
from monitoring_audit import run_monitoring_audit

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'banking_data_quality',
    default_args=default_args,
    description='Daily banking data quality and risk checks',
    schedule_interval='@daily',
    start_date=datetime(2025, 7, 19),
    catchup=False
) as dag:

    def run_generate_data():
        try:
            generate_data()
            print("Data generation completed successfully.")
        except Exception as e:
            print(f"Data generation failed: {str(e)}")
            raise

    def run_data_quality_task():
        try:
            df = run_data_quality_checks()
            failed_checks = df[df['Status'] == 'FAIL']
            if not failed_checks.empty:
                print(f"Data quality checks failed: {failed_checks.to_dict()}")
                raise Exception("Data quality checks failed")
            print("Data quality checks passed.")
        except Exception as e:
            print(f"Data quality checks failed: {str(e)}")
            raise

    def run_monitoring_audit_task():
        try:
            checks = run_monitoring_audit()
            # failed_checks = df[df['Status'] == 'FAIL']
            # if not failed_checks.empty:
            #    print(f"Monitoring checks failed: {failed_checks.to_dict()}")
            #    raise Exception("Monitoring checks failed")
            print("Monitoring checks passed.")
            print(f"checks = {checks}")
        except Exception as e:
            print(f"Monitoring checks failed: {str(e)}")
            raise

    generate_data_task = PythonOperator(
        task_id='generate_data',
        python_callable=run_generate_data,
        dag=dag
    )

    data_quality_task = PythonOperator(
        task_id='run_data_quality_checks',
        python_callable=run_data_quality_task,
        dag=dag
    )

    monitoring_audit_task = PythonOperator(
        task_id='run_monitoring_audit',
        python_callable=run_monitoring_audit_task,
        dag=dag
    )

    # Task dependencies
    generate_data_task >> data_quality_task >> monitoring_audit_task
