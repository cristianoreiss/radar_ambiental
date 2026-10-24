import os
import polars as pl
from pathlib import Path

CAMINHO_PASTA_RAW = Path("data/raw")
CAMINHO_PASTA_BRONZE = Path("data/bronze")
CAMINHO_DADOS_QUALITY = CAMINHO_PASTA_RAW / "air-quality_raw.json"
CAMINHO_DADOS_FORECAST = CAMINHO_PASTA_RAW / "forecast_raw.json"
os.makedirs(CAMINHO_PASTA_BRONZE, exist_ok=True)

dataframe_forecast = pl.read_json(CAMINHO_DADOS_FORECAST)
dataframe_quality = pl.read_json(CAMINHO_DADOS_QUALITY)

campos_units_forecast = dataframe_forecast["hourly_units"].struct.fields
campo_valores_forecast = dataframe_forecast["hourly"].struct.fields
dataframe_forecast = dataframe_forecast.with_columns(
    pl.col("hourly_units").struct.rename_fields([f"{c}_unit" for c in campos_units_forecast])
)
dataframe_forecast = dataframe_forecast.unnest().explode(columns=campo_valores_forecast)

campo_units_quality = dataframe_quality["hourly_units"].struct.fields
campo_valores_quality = dataframe_quality["hourly"].struct.fields
dataframe_quality = dataframe_quality.with_columns(
    pl.col("hourly_units").struct.rename_fields([f"{c}_unit" for c in campo_units_quality])
)
dataframe_quality = dataframe_quality.unnest().explode(columns=campo_valores_quality)

dataframe_forecast.write_parquet(CAMINHO_PASTA_BRONZE / "forecast_bronze.parquet")
dataframe_quality.write_parquet(CAMINHO_PASTA_BRONZE / "air-quality_bronze.parquet")