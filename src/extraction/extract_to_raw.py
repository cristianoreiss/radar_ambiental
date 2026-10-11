import requests

r = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-23.55&longitude=-46.63&hourly=temperature_2m&timezone=UTC")
print(r.json())