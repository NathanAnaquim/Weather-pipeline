"""
Etapa de Carga (Load) do pipeline.
Lê os CSVs tratados da pasta processed/, cria (se necessário) o banco e a
tabela no MySQL, e insere os dados, evitando duplicatas.
"""

import glob
import os

import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DIR = "processed"
TABLE_NAME = "clima"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
}
DB_NAME = os.getenv("DB_NAME", "weather_pipeline")

CREATE_DB_SQL = f"CREATE DATABASE IF NOT EXISTS {DB_NAME};"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cidade VARCHAR(100) NOT NULL,
    pais VARCHAR(10),
    temperatura_c FLOAT,
    sensacao_termica_c FLOAT,
    temp_min_c FLOAT,
    temp_max_c FLOAT,
    amplitude_termica_c FLOAT,
    umidade_pct INT,
    pressao_hpa INT,
    descricao VARCHAR(255),
    vento_velocidade_ms FLOAT,
    nuvens_pct INT,
    timestamp_coleta_unix BIGINT,
    data_hora_coleta DATETIME,
    arquivo_origem VARCHAR(255),
    UNIQUE KEY uniq_cidade_timestamp (cidade, timestamp_coleta_unix)
);
"""

INSERT_SQL = f"""
INSERT IGNORE INTO {TABLE_NAME} (
    cidade, pais, temperatura_c, sensacao_termica_c, temp_min_c, temp_max_c,
    amplitude_termica_c, umidade_pct, pressao_hpa, descricao,
    vento_velocidade_ms, nuvens_pct, timestamp_coleta_unix,
    data_hora_coleta, arquivo_origem
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""


def load_all_processed_csvs() -> pd.DataFrame:
    """Lê e junta todos os CSVs tratados encontrados em processed/."""
    filepaths = glob.glob(f"{PROCESSED_DIR}/*.csv")

    if not filepaths:
        raise FileNotFoundError(
            f"Nenhum arquivo .csv encontrado em '{PROCESSED_DIR}/'. "
            "Rode transform_weather.py primeiro."
        )

    dfs = [pd.read_csv(fp) for fp in filepaths]
    df = pd.concat(dfs, ignore_index=True)
    df = df.drop_duplicates(subset=["cidade", "timestamp_coleta_unix"])

    print(f"[OK] {len(filepaths)} CSV(s) carregado(s), {len(df)} linha(s) únicas no total")
    return df


def ensure_database_exists() -> None:
    """Conecta sem especificar banco e cria o banco se ele não existir."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(CREATE_DB_SQL)
    conn.commit()
    cursor.close()
    conn.close()


def load_to_db(df: pd.DataFrame) -> None:
    """Cria a tabela (se não existir) e insere os dados, ignorando duplicatas."""
    conn = mysql.connector.connect(database=DB_NAME, **DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)

    rows = df[[
        "cidade", "pais", "temperatura_c", "sensacao_termica_c",
        "temp_min_c", "temp_max_c", "amplitude_termica_c", "umidade_pct",
        "pressao_hpa", "descricao", "vento_velocidade_ms", "nuvens_pct",
        "timestamp_coleta_unix", "data_hora_coleta", "arquivo_origem",
    ]].values.tolist()

    cursor.executemany(INSERT_SQL, rows)
    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total_na_tabela = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print(f"[OK] Dados inseridos no banco '{DB_NAME}' (tabela '{TABLE_NAME}')")
    print(f"[OK] Total de registros na tabela agora: {total_na_tabela}")


def main():
    try:
        df = load_all_processed_csvs()
        ensure_database_exists()
        load_to_db(df)
    except Error as e:
        print(f"[ERRO] Falha na conexão/operação com o MySQL: {e}")


if __name__ == "__main__":
    main()
