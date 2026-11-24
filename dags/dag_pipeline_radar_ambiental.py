import pendulum
from datetime import timedelta
from airflow.sdk import dag, task
from src.extraction.extract_to_raw import (
    extract_to_raw,
    CAMINHO_ARQUIVO_CAPITAIS,
    CAMINHO_PASTA_RAW,
    DADOS_API
) 
from src.transformation.raw_to_bronze import (
    raw_to_bronze,
    CAMINHO_PASTA_RAW,
    CAMINHO_PASTA_BRONZE,
    ARQUIVOS_RAW
)
raw_to_bronze
from src.transformation.bronze_to_silver import (
    bronze_to_silver,
    CAMINHO_PASTA_BRONZE,
    CAMINHO_PASTA_SILVER,
    ARQUIVOS_BRONZE,
    EXCLUIR_COLUNAS
) 
from src.transformation.silver_to_gold import (
    silver_to_gold,
    CAMINHO_PASTA_SILVER,
    CAMINHO_PASTA_GOLD,
    CAMINHO_LOCATIONS
)

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
        extract_to_raw(
            caminho_arquivo_capitais=CAMINHO_ARQUIVO_CAPITAIS,
            caminho_raw = CAMINHO_PASTA_RAW,
            configuracoes_api=DADOS_API
        )

    @task(execution_timeout=timedelta(minutes=30))
    def task_raw_to_bronze():
        raw_to_bronze(
            pasta_raw=CAMINHO_PASTA_RAW,
            pasta_bronze=CAMINHO_PASTA_BRONZE,
            lista_arquivo=ARQUIVOS_RAW
        )

    @task(execution_timeout=timedelta(minutes=30))
    def task_bronze_to_silver():
        bronze_to_silver(
            pasta_bronze=CAMINHO_PASTA_BRONZE,
            pasta_silver=CAMINHO_PASTA_SILVER,
            lista_arquivo=ARQUIVOS_BRONZE,
            colunas_excluir=EXCLUIR_COLUNAS
        )

    @task(execution_timeout=timedelta(minutes=30))
    def task_silver_to_gold():
        silver_to_gold(
            pasta_silver=CAMINHO_PASTA_SILVER,
            pasta_gold=CAMINHO_PASTA_GOLD,
            caminho_locations=CAMINHO_LOCATIONS
        )

    task_extract() >> task_raw_to_bronze() >> task_bronze_to_silver() >> task_silver_to_gold()

pipeline_radar_ambiental()