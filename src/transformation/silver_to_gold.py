from pathlib import Path
import polars as pl

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_SILVER_FORECAST = PASTA_PROJETO / "data/silver/forecast_silver.parquet"
CAMINHO_SILVER_QUALITY = PASTA_PROJETO / "data/silver/air-quality_silver.parquet"
CAMINHO_PASTA_GOLD = PASTA_PROJETO / "data/gold"
CAMINHO_PASTA_GOLD.mkdir(parents=True,exist_ok=True)

dataset_forecast = pl.read_parquet(CAMINHO_SILVER_FORECAST)
dataset_quality = pl.read_parquet(CAMINHO_SILVER_QUALITY)

