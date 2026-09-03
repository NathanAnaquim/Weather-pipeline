"""
Etapa de Transformação (Transform) do pipeline.
Lê os JSONs brutos da pasta raw/, estrutura num DataFrame,
limpa e calcula métricas, e salva o resultado tratado em processed/.
"""

import os
import json
import glob
from datetime import datetime, timezone

import pandas as pd

RAW_DIR = "raw"
PROCESSED_DIR = "processed"


def load_raw_files() -> list[dict]:
    """Lê todos os arquivos JSON da pasta raw/ e retorna uma lista de dicts."""
    filepaths = glob.glob(f"{RAW_DIR}/*.json")

    if not filepaths:
        raise FileNotFoundError(
            f"Nenhum arquivo .json encontrado em '{RAW_DIR}/'. "
            "Rode extract_weather.py primeiro."
        )

    records = []
    for filepath in filepaths:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_source_file"] = os.path.basename(filepath)
            records.append(data)

    print(f"[OK] {len(records)} arquivos carregados de '{RAW_DIR}/'")
    return records


def flatten_record(record: dict) -> dict:
    """
    Extrai só os campos relevantes de um registro bruto da API,
    que vem com estrutura aninhada (main, weather, wind, etc.).
    """
    try:
        return {
            "cidade": record.get("name"),
            "pais": record.get("sys", {}).get("country"),
            "temperatura_c": record.get("main", {}).get("temp"),
            "sensacao_termica_c": record.get("main", {}).get("feels_like"),
            "temp_min_c": record.get("main", {}).get("temp_min"),
            "temp_max_c": record.get("main", {}).get("temp_max"),
            "umidade_pct": record.get("main", {}).get("humidity"),
            "pressao_hpa": record.get("main", {}).get("pressure"),
            "descricao": record.get("weather", [{}])[0].get("description"),
            "vento_velocidade_ms": record.get("wind", {}).get("speed"),
            "nuvens_pct": record.get("clouds", {}).get("all"),
            "timestamp_coleta_unix": record.get("dt"),
            "arquivo_origem": record.get("_source_file"),
        }
    except (KeyError, IndexError, TypeError) as e:
        print(f"[AVISO] Registro mal formado, pulando: {e}")
        return {}


def transform(records: list[dict]) -> pd.DataFrame:
    """Aplica a transformação em todos os registros e retorna um DataFrame limpo."""
    flattened = [flatten_record(r) for r in records]
    flattened = [r for r in flattened if r]  # remove registros vazios/mal formados

    df = pd.DataFrame(flattened)

    # Converte timestamp Unix para data/hora legível
    df["data_hora_coleta"] = pd.to_datetime(
        df["timestamp_coleta_unix"], unit="s", utc=True
    )

    # Remove duplicatas exatas (mesma cidade + mesmo timestamp de coleta)
    linhas_antes = len(df)
    df = df.drop_duplicates(subset=["cidade", "timestamp_coleta_unix"])
    duplicatas_removidas = linhas_antes - len(df)
    if duplicatas_removidas > 0:
        print(f"[OK] {duplicatas_removidas} duplicata(s) removida(s)")

    # Remove linhas sem temperatura (dado essencial ausente)
    df = df.dropna(subset=["temperatura_c"])

    # Calcula amplitude térmica do dia
    df["amplitude_termica_c"] = df["temp_max_c"] - df["temp_min_c"]

    # Ordena por cidade e data
    df = df.sort_values(["cidade", "data_hora_coleta"]).reset_index(drop=True)

    return df


def save_processed(df: pd.DataFrame) -> str:
    """Salva o DataFrame tratado em CSV."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = f"{PROCESSED_DIR}/clima_tratado_{timestamp}.csv"
    df.to_csv(filepath, index=False, encoding="utf-8")
    print(f"[OK] Dados tratados salvos em {filepath}")
    return filepath


def main():
    records = load_raw_files()
    df = transform(records)

    print("\n--- Resumo dos dados tratados ---")
    print(f"Total de registros: {len(df)}")
    print(f"Cidades: {df['cidade'].unique().tolist()}")
    print(f"Período: {df['data_hora_coleta'].min()} até {df['data_hora_coleta'].max()}")
    print("\nPrévia:")
    print(df.head())

    save_processed(df)


if __name__ == "__main__":
    main()
