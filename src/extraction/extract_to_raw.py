import requests
import json
import os
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_RAW = "data/raw"
CAMINHO_ARQUIVO_CAPITAIS = PASTA_PROJETO / "config" / "locations.json"

DADOS_API = [
    {
        "nome": "air-quality",
        "endpoint": "https://air-quality-api.open-meteo.com/v1/air-quality",
        "campos": "pm10,pm2_5,ozone"
    },
    {
        "nome": "forecast",
        "endpoint": "https://api.open-meteo.com/v1/forecast",
        "campos": "precipitation_probability,temperature_2m,precipitation,relative_humidity_2m"
    }
]

######################################################

def ler_dados_capitais(caminho_arquivo_capitais: str | Path) -> list[dict]:
    with open(caminho_arquivo_capitais,"r",encoding="utf-8") as arquivo:
        lista_capitais = json.load(arquivo)
    return lista_capitais

def consultar_api(url:str, sessao:requests.Session, latitude:float,longitude:float,campos:str) -> dict:
    parametros = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly":campos,
        "timezone": "UTC"
    }
    resposta = sessao.get(url=url,params=parametros)
    dados = resposta.json()
    return dados

def gravar_na_raw(pasta: str | Path, nome_arquivo: str,lista_dados:list[dict]) -> None:
    pasta = Path(pasta)
    nome_arquivo_extensao = "raw_" + nome_arquivo + ".json"
    pasta.mkdir(parents=True,exist_ok=True)
    caminho_arquivo = pasta / nome_arquivo_extensao
    with open(caminho_arquivo,"w",encoding="utf-8") as arquivo:
        json.dump(lista_dados,arquivo,indent=4,ensure_ascii=False)

def extract_to_raw() -> None:
    sessao = requests.Session()
    lista_capitais = ler_dados_capitais(CAMINHO_ARQUIVO_CAPITAIS)

    for api in DADOS_API:
        nome = api["nome"]
        endpoint = api["endpoint"]
        campos = api["campos"]
        api["dados_api"] = []
        for capital in lista_capitais:
            uf = capital["uf"]
            nome_capital = capital["name"]
            latitude = capital["latitude"]
            longitude = capital["longitude"]
            dados_api = consultar_api(url=endpoint,sessao=sessao,latitude=latitude,longitude=longitude,campos=campos)
            dados_api["uf"] = uf
            dados_api["name"] = nome_capital
            api["dados_api"].append(dados_api)

        gravar_na_raw(pasta=CAMINHO_PASTA_RAW,nome_arquivo=nome,lista_dados=api["dados_api"])


if __name__ == "__main__":
    extract_to_raw() 

