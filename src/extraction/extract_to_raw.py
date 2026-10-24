import requests
import json
import os

CAMINHO_ARQUIVO_CAPITAIS = "config/locations.json"
CAMINHO_PASTA_RAW = "data/raw"


os.makedirs(CAMINHO_PASTA_RAW, exist_ok=True)

session = requests.Session()

with open(CAMINHO_ARQUIVO_CAPITAIS,"r",encoding="utf-8") as arquivo:
    geo_capitais = json.load(arquivo)

ENDPOINT_QUALIDADE = "https://air-quality-api.open-meteo.com/v1/air-quality"
ENDPOINT_PREVISAO = "https://api.open-meteo.com/v1/forecast"
dados_previsao = []
dados_qualidade = []

for capital in geo_capitais:
    parametros_previsao = {
        "latitude": capital.get("latitude"),
        "longitude": capital.get("longitude"),
        "hourly": "precipitation_probability,temperature_2m,precipitation,relative_humidity_2m",
        "timezone": "UTC"
    }

    try:
        resposta_previsao = session.get(url=ENDPOINT_PREVISAO,params=parametros_previsao)
        resposta_previsao.raise_for_status()
        dados = resposta_previsao.json()
        """
        dados_capital = {
            "name": capital.get("name"),
            "uf": capital.get("uf")
            "hourly": dados.get("hourly"),
            "temperature_2m": dados.get("temperature_2m"),
            "precipitation_probability": dados.get("precipitation_probability"),
            "precipitation": dados.get("precipitation"),
            "relative_humidity_2m": dados.get("relative_humidity_2m")
            
        }
        """
    except Exception as e:
        print(f"Erro encontrado: {e}")  
    else:
        dados.update({"name":capital.get("name"),"uf":capital.get("uf")})
        dados_previsao.append(dados)

    ## ============================================================

    parametros_qualidade = {
        "latitude": capital.get("latitude"),
        "longitude": capital.get("longitude"),
        "hourly": "pm10,pm2_5,ozone",
        "timezone": "UTC"
    }  

    try:
        resposta_qualidade = session.get(url=ENDPOINT_QUALIDADE,params=parametros_qualidade)
        resposta_qualidade.raise_for_status()
        dados = resposta_qualidade.json()
    except Exception as e:
        print(f"Erro encontrado: {e}")
    else:
        dados.update({"name":capital.get("name"),"uf":capital.get("uf")})
        dados_qualidade.append(dados)

# === Criar arquivo raw

caminho_forecast = os.path.join(CAMINHO_PASTA_RAW,"forecast_raw.json")
with open(caminho_forecast,"w",encoding="utf-8") as arquivo:
    json.dump(dados_previsao,arquivo,indent=4, ensure_ascii=False)

caminho_air_quality = os.path.join(CAMINHO_PASTA_RAW,"air-quality_raw.json")
with open(caminho_air_quality,"w",encoding="utf-8") as arquivo:
    json.dump(dados_qualidade,arquivo,indent=4, ensure_ascii=False)