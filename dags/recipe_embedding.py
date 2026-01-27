from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator

from lib.embedding_pipeline import run_embedding_pipeline

default_args = {
    "owner": "airflow",
    "start_date": datetime(2026, 1, 9),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="recipe_embedding",
    default_args=default_args,
    schedule_interval="*/10 * * * *",
    max_active_runs=1,
    catchup=False,
    tags=["ai-tech"],
) as dag:

    embed_recipes = PythonOperator(
        task_id="embed_recipes",
        python_callable=run_embedding_pipeline,
        op_kwargs={"limit": 50},
    )

    embed_recipes
