import requests
from pathlib import Path
import polars as pl
import json
import logging


logger = logging.getLogger(__name__)

URL_GEO = "https://geocoding-api.open-meteo.com/v1/search"


################################################################################

def ler_capitais(caminho_arquivo: str | Path) -> list[dict]:
    try:
        df_capitais = pl.read_csv(caminho_arquivo)
    except FileNotFoundError:
        logger.exception("Arquivo das capitais não encontrado: %s", caminho_arquivo)
        raise
    except pl.exceptions.NoDataError:
        logger.exception("Arquivo referenciado vazio: %s", caminho_arquivo)
        raise
    logger.info("Importação do arquivo das capitais concluída")
    dict_capitais = df_capitais.to_dicts()
    return dict_capitais

def buscar_candidatos(sessao:requests.Session,capital:str,url:str) -> list:
    parametros = {
        "name":capital,
        "countryCode":"BR"
    }
    try:
        resultado = sessao.get(url=url,params=parametros,timeout=10)
        resultado.raise_for_status() # verifica o cód do status HTTP e lança uma exceção caso retorne um erro HTTP
    except requests.exceptions.HTTPError as erro:
        logger.exception("API indisponível: %s", erro)
    lista_candidatos = resultado.json().get("results",[])
    logger.info("Lista de cidades candidatas gerada")
    return lista_candidatos

def escolher_capital(lista_candidatos:list):
    cidade = [candidato for candidato in lista_candidatos if candidato if candidato.get("feature_code") in ["PPLA","PPLC"]]
    if len(cidade) != 1:
        raise ValueError(f"Esperado 1 candidato,encontrado {len(cidade)}")
    cidade_capital = cidade[0]
    return cidade_capital

def formatar_capital(uf:str,candidato:dict) -> dict:
    cidade_formatada = {
        "name":candidato["name"],
        "uf":uf,
        "latitude":candidato["latitude"],
        "longitude":candidato["longitude"],
        "timezone":candidato["timezone"],
    }
    return cidade_formatada

def gravar_locations(lista_cidade:list,pasta:str | Path,nome_arquivo:str) -> None:
    pasta = Path(pasta)
    pasta.mkdir(parents=True,exist_ok=True)
    caminho = pasta / nome_arquivo
    with open(caminho,"w",encoding="utf-8") as arquivo:
        json.dump(lista_cidade,arquivo,indent=4, ensure_ascii=False)

def gerar_geolocalizacao_capitais() -> None:
    sessao = requests.Session()
    dados_capitais = []

    dict_capitais = ler_capitais(caminho_arquivo="config/capitais.csv")
    for cidade in dict_capitais:
        lista_candidatos = buscar_candidatos(sessao=sessao,capital=cidade["capital"],url=URL_GEO)
        capital = escolher_capital(lista_candidatos=lista_candidatos)
        capital_formatada = formatar_capital(uf = cidade["uf"],candidato=capital)
        dados_capitais.append(capital_formatada)
    gravar_locations(lista_cidade=dados_capitais,pasta="config",nome_arquivo="locations.json")

if __name__ == "__main__":
    gerar_geolocalizacao_capitais()