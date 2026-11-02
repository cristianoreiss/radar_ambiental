import requests
import json
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parents[2]
CAMINHO_PASTA_RAW = PASTA_PROJETO / "data" / "raw"
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

def extract_to_raw(
        caminho_arquivo_capitais: Path,
        caminho_raw: Path,
        configuracoes_api: list[dict]
) -> None:
    sessao = requests.Session()
    lista_capitais = ler_dados_capitais(caminho_arquivo_capitais)

    for api in configuracoes_api:
        nome = api["nome"]
        endpoint = api["endpoint"]
        campos = api["campos"]

        lista_dados = []

        for capital in lista_capitais:
            dados_resposta = consultar_api(
                url=endpoint,
                sessao=sessao,
                latitude=capital["latitude"],
                longitude=capital["longitude"],
                campos=campos
            )
            dados_resposta["uf"] = capital["uf"]
            dados_resposta["name"] = capital["name"]

            lista_dados.append(dados_resposta)

        gravar_na_raw(
            pasta=caminho_raw,
            nome_arquivo=nome,
            lista_dados=lista_dados
        )


if __name__ == "__main__":
    extract_to_raw(
        caminho_arquivo_capitais = CAMINHO_ARQUIVO_CAPITAIS,
        caminho_raw = CAMINHO_PASTA_RAW,
        configuracoes_api=DADOS_API
    ) 

