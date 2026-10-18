import os
import requests
import json

CAMINHO_PASTA_RAW = "data/raw"
CAMINHO_PASTA_BRONZE = "data/bronze"
CAMINHO_DADOS_QUALITY = CAMINHO_PASTA_RAW.join("/air-quality_raw.json")
CAMINHO_DADOS_FORECAST = CAMINHO_PASTA_RAW.join("/forecast_raw.json")
os.makedirs(CAMINHO_PASTA_BRONZE, exist_ok=True)

json_forecast = []
json_quality = []

with open(CAMINHO_DADOS_FORECAST,"r",encoding="utf-8") as arquivo_forecast:
    json_forecast = json.load(arquivo_forecast)

with open(CAMINHO_DADOS_QUALITY,"r",encoding="utf-8") as arquivo_quality:
    json_quality = json.load(arquivo_quality)

