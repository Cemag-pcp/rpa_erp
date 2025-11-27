import os
from pathlib import Path
from typing import Dict, Optional

import psycopg2


BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_LOADED = False
_ACTIVE_SCHEMA: Optional[str] = None


def _load_env() -> None:
    """
    Carrega variáveis do arquivo .env da raiz do projeto,
    sem sobrescrever variáveis já definidas no ambiente.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().rstrip(",")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except Exception:
            # Em caso de erro na leitura, apenas segue com o ambiente atual
            pass

    _ENV_LOADED = True


def get_db_config() -> Dict[str, str]:
    """
    Retorna o dicionário de configuração de conexão com o PostgreSQL
    usando variáveis de ambiente (carregadas do .env se existir).
    """
    _load_env()
    return {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
    }


def get_db_connection():
    """
    Abre uma nova conexão com o banco usando psycopg2.
    """
    config = get_db_config()
    return psycopg2.connect(**config)


def get_active_schema() -> Optional[str]:
    """
    Retorna o schema ativo para tabelas de RPA.
    DB_SCHEMA_DEPLOY tem prioridade; se não houver, usa DB_SCHEMA_TEST.
    """
    global _ACTIVE_SCHEMA
    if _ACTIVE_SCHEMA is None:
        _load_env()
        _ACTIVE_SCHEMA = os.getenv("DB_SCHEMA_DEPLOY") or os.getenv("DB_SCHEMA_TEST")
    return _ACTIVE_SCHEMA


def get_schedule_table_name(default: str = "rpa_bot_schedule") -> str:
    """
    Nome base da tabela de agendamento.
    Pode ser sobrescrito com DB_RPA_SCHEDULE_TABLE.
    """
    _load_env()
    return os.getenv("DB_RPA_SCHEDULE_TABLE", default)


def get_erp_credentials_table_name(default: str = "rpa_bot_erp_credentials") -> str:
    """
    Nome base da tabela que guarda login/senha do ERP por bot.
    Pode ser sobrescrito com DB_ERP_CREDENTIALS_TABLE.
    """
    _load_env()
    return os.getenv("DB_ERP_CREDENTIALS_TABLE", default)


def get_erp_credentials_for_bot(bot_name: str) -> Dict[str, str]:
    """
    Retorna um dicionário com credenciais ERP para um bot específico:
      { "erp_username": "...", "erp_password": "..." }
    Se não encontrar, retorna dicionário vazio.
    """
    schema = get_active_schema()
    table = get_erp_credentials_table_name()
    full_table = f"{schema}.{table}" if schema else table

    try:
        conn = get_db_connection()
    except Exception:
        return {}

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT erp_username, erp_password FROM {full_table} WHERE bot_name = %s",
                    (bot_name,),
                )
                row = cur.fetchone()
                if not row:
                    return {}
                username, password = row
                return {
                    "erp_username": username,
                    "erp_password": password,
                }
    except Exception:
        return {}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_headless_mode_for_bot(bot_name: str) -> bool:
    """
    Retorna True/False indicando se o bot deve rodar em headless, de acordo
    com a tabela de agendamento (headless_mode).
    Se não houver registro, assume False.
    """
    schema = get_active_schema()
    table = get_schedule_table_name()
    full_table = f"{schema}.{table}" if schema else table

    try:
        conn = get_db_connection()
    except Exception:
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT headless_mode FROM {full_table} WHERE bot_name = %s",
                    (bot_name,),
                )
                row = cur.fetchone()
                if not row:
                    return False
                (headless_mode,) = row
                return bool(headless_mode)
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
