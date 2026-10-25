import polars as pl
import polars.selectors as cs
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_BRONZE = PASTA_PROJETO / "data/bronze"
CAMINHO_PASTA_SILVER = PASTA_PROJETO / "data/silver"
CAMINHO_DADOS_QUALITY = CAMINHO_PASTA_BRONZE / "air-quality_bronze.parquet"
CAMINHO_DADOS_FORECAST = CAMINHO_PASTA_BRONZE / "forecast_bronze.parquet"
CAMINHO_PASTA_SILVER.mkdir(parents=True,exist_ok=True)
EXCLUIR_COLUNAS = ["latitude","longitude","generationtime_ms","utc_offset_seconds","timezone","timezone_abbreviation","elevation"]

dataset_forecast = pl.read_parquet(CAMINHO_DADOS_FORECAST)
dataset_quality = pl.read_parquet(CAMINHO_DADOS_QUALITY)

dataset_forecast = dataset_forecast.drop(
    cs.ends_with("_unit"),
    EXCLUIR_COLUNAS
    strict=False
)
dataset_quality = dataset_quality.drop(
    cs.ends_with("_unit"),
    EXCLUIR_COLUNAS,
    strict=False
)

dataset_forecast = dataset_forecast.with_columns([
    pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M").dt.replace_time_zone("UTC")
])
dataset_quality = dataset_quality.with_columns([
    pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M").dt.replace_time_zone("UTC")
])

dataset_forecast.write_parquet(CAMINHO_PASTA_SILVER / "forecast_silver.parquet")
dataset_quality.write_parquet(CAMINHO_PASTA_SILVER / "air-quality_silver.parquet")
