from pathlib import Path
import polars as pl

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_SILVER_FORECAST = PASTA_PROJETO / "data/silver/forecast_silver.parquet"
CAMINHO_SILVER_QUALITY = PASTA_PROJETO / "data/silver/air-quality_silver.parquet"
CAMINHO_PASTA_GOLD = PASTA_PROJETO / "data/gold"
CAMINHO_PASTA_GOLD.mkdir(parents=True,exist_ok=True)

dataset_forecast = pl.read_parquet(CAMINHO_SILVER_FORECAST)
dataset_quality = pl.read_parquet(CAMINHO_SILVER_QUALITY)
dataset_capitais = pl.read_json(PASTA_PROJETO / "config/locations.json")
dataset_capitais = dataset_capitais.with_columns(
    pl.when(pl.col("uf").is_in(["RJ", "SP", "ES", "MG"]))
    .then(pl.lit("Sudeste"))
    .when(pl.col("uf").is_in(["BA", "SE", "AL", "PE", "PB", "RN", "CE", "MA", "PI"]))
    .then(pl.lit("Nordeste"))
    .when(pl.col("uf").is_in(["AM", "AP", "RR", "RO", "AC", "PA", "TO"]))
    .then(pl.lit("Norte"))
    .when(pl.col("uf").is_in(["MS", "MT", "GO", "DF"]))
    .then(pl.lit("Centro-Oeste"))
    .when(pl.col("uf").is_in(["PR", "SC", "RS"]))
    .then(pl.lit("Sul"))
    .otherwise(None)
    .alias("regiao")
)
dataset_quality = dataset_quality.drop("name")
radar_horario = dataset_forecast.join(
    dataset_quality,
    on=["uf","time"],
    how="full",
    coalesce=True
)

