import os
import polars as pl
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_RAW = PASTA_PROJETO / "data" / "raw"
CAMINHO_PASTA_BRONZE = PASTA_PROJETO / "data" / "bronze"
ARQUIVOS_RAW = [
    "raw_forecast.json",
    "raw_air-quality.json"
]

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

dataframe_forecast.write_parquet(CAMINHO_PASTA_BRONZE / "bronze_forecast.parquet")
dataframe_quality.write_parquet(CAMINHO_PASTA_BRONZE / "bronze_air-quality.parquet")

def ler_dados_raw(
        caminho_raw: Path,
        nome_arquivo: str
) -> list[dict]:
    caminho_arquivo = caminho_raw / nome_arquivo
    dataframe = pl.read_json(caminho_arquivo)
    



def converter_em_parquet() ->:

def gravar_dados_bronze():

def raw_to_bronze():
