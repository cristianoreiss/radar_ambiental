import polars as pl
import polars.selectors as cs
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_BRONZE = PASTA_PROJETO / "data" / "bronze"
CAMINHO_PASTA_SILVER = PASTA_PROJETO / "data" / "silver"
EXCLUIR_COLUNAS = ["latitude","longitude","generationtime_ms","utc_offset_seconds","timezone","timezone_abbreviation","elevation"]
ARQUIVOS_BRONZE = [
    "bronze_forecast.parquet",
    "bronze_air-quality.parquet"
]

def ler_dados_bronze(
        caminho_bronze: Path,
        nome_arquivo: str
) -> pl.DataFrame:
    caminho_arquivo = caminho_bronze / nome_arquivo
    dataframe = pl.read_parquet(caminho_arquivo)
    return dataframe

def renomear_campos_unidades(
        dataframe: pl.DataFrame,
) -> pl.DataFrame:
    campos_unit = dataframe["hourly_units"].struct.fields
    dataframe = dataframe.with_columns(
        pl.col("hourly_units").struct.rename_fields([f"{c}_unit" for c in campos_unit])
    )
    return dataframe

def expandir_estruturas(
    dataframe: pl.DataFrame
) -> pl.DataFrame:
    campos_valores = dataframe["hourly"].struct.fields
    # unnest expande as estruturas struct e transforma em colunas e explode transforma os elementos de uma lista em linhas individuais
    dataframe = dataframe.unnest().explode(columns=campos_valores)
    return dataframe

def transformar_dataset(
        caminho_bronze: Path,
        nome_arquivo: str,
        colunas_excluir: list[str]
) -> pl.DataFrame:
    
    dataframe = ler_dados_bronze(
        caminho_bronze=caminho_bronze,
        nome_arquivo=nome_arquivo
    )

    dataframe = renomear_campos_unidades(dataframe=dataframe)

    dataframe = expandir_estruturas(dataframe=dataframe)

    dataframe = dataframe.drop(
        cs.ends_with("_unit"),
        colunas_excluir,
        strict=False
    )

    dataframe = dataframe.with_columns(
        pl.col("time")
        .str.to_datetime("%Y-%m-%dT%H:%M")
        .dt.replace_time_zone("UTC")
    )

    return dataframe

def gravar_parquet_silver(
        dataframe: pl.DataFrame,
        pasta_destino: Path,
        nome_arquivo_fonte: str
) -> None:
    nome_arquivo = Path(nome_arquivo_fonte).stem.removeprefix("bronze_")
    pasta_destino.mkdir(parents=True, exist_ok=True)
    caminho_arquivo = pasta_destino / f"silver_{nome_arquivo}.parquet"
    dataframe.write_parquet(caminho_arquivo)

def bronze_to_silver(
        pasta_bronze: Path,
        pasta_silver: Path,
        lista_arquivo: list[str],
        colunas_excluir: list[str]
) -> None:
    for arquivo in lista_arquivo:
        dataframe = transformar_dataset(
            caminho_bronze=pasta_bronze,
            nome_arquivo=arquivo,
            colunas_excluir=colunas_excluir
        )

        gravar_parquet_silver(
            dataframe=dataframe,
            pasta_destino=pasta_silver,
            nome_arquivo_fonte=arquivo
        )

if __name__ == "__main__":
    bronze_to_silver(
        pasta_bronze=CAMINHO_PASTA_BRONZE,
        pasta_silver=CAMINHO_PASTA_SILVER,
        lista_arquivo=ARQUIVOS_BRONZE,
        colunas_excluir=EXCLUIR_COLUNAS
    )
