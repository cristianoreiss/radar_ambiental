import polars as pl
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_RAW = PASTA_PROJETO / "data" / "raw"
CAMINHO_PASTA_BRONZE = PASTA_PROJETO / "data" / "bronze"
ARQUIVOS_RAW = [
    "raw_forecast.json",
    "raw_air-quality.json"
]

def ler_dados_raw(
        caminho_raw: Path,
        nome_arquivo: str
) -> pl.DataFrame:
    caminho_arquivo = caminho_raw / nome_arquivo
    dataframe = pl.read_json(caminho_arquivo)
    return dataframe

def gravar_parquet_bronze(
        dataframe:pl.DataFrame,
        pasta_destino: Path,
        nome_arquivo_fonte: str
) -> None:
    nome_arquivo = Path(nome_arquivo_fonte).stem.removeprefix("raw_") ## stem para retornar nome arquivo sem extensão
    caminho_arquivo = pasta_destino / f"bronze_{nome_arquivo}.parquet"
    dataframe.write_parquet(caminho_arquivo)
    

def raw_to_bronze(
        pasta_raw: Path,
        pasta_bronze: Path,
        lista_arquivo: list[str]
) -> None:
    for arquivo in lista_arquivo:
        dataframe = ler_dados_raw(
            caminho_raw=pasta_raw,
            nome_arquivo=arquivo
        )
        gravar_parquet_bronze(
            dataframe=dataframe,
            pasta_destino=pasta_bronze,
            nome_arquivo_fonte=arquivo
        )

if __name__ == "__main__":
    raw_to_bronze(
        pasta_raw=CAMINHO_PASTA_RAW,
        pasta_bronze=CAMINHO_PASTA_BRONZE,
        lista_arquivo=ARQUIVOS_RAW
    ) 
