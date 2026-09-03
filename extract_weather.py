"""
Etapa de Extração (Extract) do pipeline.
Busca dados de clima na OpenWeather API e salva o retorno bruto em JSON.
"""

import os
import json
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()  # carrega variáveis do arquivo .env

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Cidades que vou monitorar
CITIES = ["Sao Paulo,BR", "Rio de Janeiro,BR", "Belo Horizonte,BR"]

RAW_DIR = "raw"


def fetch_weather(city: str) -> dict | None:
    """Busca o clima atual de uma cidade. Retorna None em caso de erro."""
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",  # Celsius em vez de Kelvin
        "lang": "pt_br",
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"[ERRO] Timeout ao buscar dados de {city}")
    except requests.exceptions.HTTPError as e:
        print(f"[ERRO] HTTP {response.status_code} ao buscar {city}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao buscar {city}: {e}")

    return None


def save_raw(city: str, data: dict) -> None:
    """Salva o JSON bruto com timestamp no nome do arquivo."""
    os.makedirs(RAW_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_city_name = city.split(",")[0].replace(" ", "_").lower()
    filename = f"{RAW_DIR}/{safe_city_name}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Dados de {city} salvos em {filename}")


def main():
    if not API_KEY:
        raise ValueError(
            "OPENWEATHER_API_KEY não encontrada. "
            "Copie .env.example para .env e adicione sua chave."
        )

    for city in CITIES:
        data = fetch_weather(city)
        if data:
            save_raw(city, data)
        time.sleep(1)  # evita bater no rate limit da API


if __name__ == "__main__":
    main()
