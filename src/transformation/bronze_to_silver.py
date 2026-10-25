import polars as pl
from pathlib import Path
import os

CAMINHO_PASTA_BRONZE = Path("data/bronze")
CAMINHO_PASTA_SILVER = Path("data/silver")
CAMINHO_DADOS_QUALITY = CAMINHO_PASTA_BRONZE / "air-quality_bronze.parquet"
CAMINHO_DADOS_FORECAST = CAMINHO_PASTA_BRONZE / "forecast_bronze.parquet"
os.makedirs(CAMINHO_PASTA_SILVER, exist_ok=True)

dataset_forecast = pl.read_parquet(CAMINHO_DADOS_FORECAST)
dataset_quality = pl.read_parquet(CAMINHO_DADOS_QUALITY)

colunas_remover_forecast = [coluna for coluna in dataset_forecast.columns if coluna.endswith("_unit")]
colunas_remover_quality = [coluna for coluna in dataset_quality.columns if coluna.endswith("_unit")]

dataset_forecast = dataset_forecast.drop(colunas_remover_forecast)
dataset_quality = dataset_quality.drop(colunas_remover_quality)
dataset_forecast = dataset_forecast.with_columns([
    pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M").dt.replace_time_zone("UTC")
])
dataset_quality = dataset_quality.with_columns([
    pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M").dt.replace_time_zone("UTC")
])

dataset_forecast.write_parquet(CAMINHO_PASTA_SILVER / "forecast_silver.parquet")
dataset_quality.write_parquet(CAMINHO_PASTA_SILVER / "air-quality_silver.parquet")