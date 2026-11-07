import pendulum
from datetime import timedelta
from airflow.sdk import dag, task
from src.extraction.extract_to_raw import extract_to_raw
from src.transformation.raw_to_bronze import raw_to_bronze
from src.transformation.bronze_to_silver import bronze_to_silver
from src.transformation.silver_to_gold import silver_to_gold

@dag(
    start_date = pendulum.datetime(
        2026, 11, 7, 16,
        tz = "America/Sao_Paulo"
    ),
    schedule="@hourly",
    default_args={
        "owner": "Cristiano",
        "retries":2,
        "retry_delay":timedelta(minutes=5)
    },
    catchup=False,
    tags=["radar-ambiental", "data-engineering"]
)

def pipeline_radar_ambiental():

    @task(execution_timeout=timedelta(minutes=30))
    def task_extract():
        extract_to_raw()

    @task(execution_timeout=timedelta(minutes=30))
    def task_raw_to_bronze():
        raw_to_bronze()

    @task(execution_timeout=timedelta(minutes=30))
    def task_bronze_to_silver():
        bronze_to_silver()

    @task(execution_timeout=timedelta(minutes=30))
    def task_silver_to_gold():
        silver_to_gold()

    task_extract() >> task_raw_to_bronze() >> task_bronze_to_silver() >> task_silver_to_gold()

pipeline_radar_ambiental()