from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from lib.mongo_to_neo4j import run_batch


default_args = {
    "owner": "airflow",
    "start_date": datetime(2026, 2, 26),
}

with DAG(
    dag_id="recipe_graph_rag",
    default_args=default_args,
    schedule_interval="*/5 * * * *",
    max_active_runs=1,
    catchup=False,
    tags=["ai-tech"],
) as dag:
    graph_rag = PythonOperator(task_id="graph_rag_recipes", python_callable=run_batch)
