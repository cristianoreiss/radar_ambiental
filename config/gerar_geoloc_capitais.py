import requests
import pandas as pd

dados_capitais = []

df_capitais = pd.read_csv("config/capitais.csv")
dict_capitais = df_capitais.to_dict(orient='records')

url_geo = "https://geocoding-api.open-meteo.com/v1/search"

for cidade in dict_capitais:
    parametros = {
        "name":cidade["capital"],
        "countryCode":"BR"
    }
    r = requests.get(url=url_geo, params=parametros, timeout=10)
    candidatos = r.json().get("results",[])
    capitais = [item for item in candidatos if item.get("feature_code") in ["PPLA","PPLC"]]
    if len(capitais) == 1:
        cidade_certa = capitais[0]
        cidade_formatada = {
            "name": cidade_certa["name"],
            "uf":cidade["uf"],
            "latitude":cidade_certa["latitude"],
            "longitude":cidade_certa["longitude"],
            "timezone":cidade_certa["timezone"],
        }
        dados_capitais.append(cidade_formatada)
    else:
        print("Mais de uma cidade disponível")
    


