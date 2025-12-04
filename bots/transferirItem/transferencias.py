import os
import json
import requests
from psycopg2.extras import DictCursor  # Para retornar resultados como dicionários
from dotenv import load_dotenv

from core.db import get_db_connection


def verificar_transferencias():
    try:
        # Conectar ao banco de dados PostgreSQL usando configuração do .env
        conn = get_db_connection()

        cursor = conn.cursor(cursor_factory=DictCursor)  # Usa DictCursor para obter resultados como dicionários

        # Executar a consulta com junção
        query = """
            SELECT
                st.id,
                st.quantidade,
                st.obs,
                st.data_solicitacao,
                f.matricula AS funcionario_nome,
                i.codigo AS item_nome,
                d.nome AS deposito_destino,
                st.data_entrega,
                st.rpa
            FROM
                apontamento_v2.solicitacao_almox_solicitacaotransferencia st
            LEFT JOIN
                apontamento_v2.cadastro_almox_funcionario f ON st.funcionario_id = f.id
            LEFT JOIN
                apontamento_v2.cadastro_almox_itenstransferencia i ON st.item_id = i.id
            LEFT JOIN
                apontamento_v2.cadastro_almox_depositodestino d ON st.deposito_destino_id = d.id
            WHERE
                st.data_entrega IS NOT NULL
                AND (st.rpa IS NULL OR st.rpa != 'OK')
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados ou executar a consulta: {e}")
        return []

    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def enviar_status_via_api(transferencia_id, status, dep_destino, rec, qtd, observacao):
    """
    Envia o status de uma requisição de transferência para a API do Django.
    """
    # --- Configuração da API ---
    DJANGO_API_URL = "https://apontamentousinagem.onrender.com/core/api/rpa/update-transfer/"
    # RPA_API_KEY = os.getenv("RPA_API_KEY")
    # ---------------------------

    payload = {
        "id": transferencia_id,
        "status": status,
        "dep_destino": dep_destino,
        "rec": rec,
        "qtd": qtd,
        "observacao": observacao,
    }
    headers = {
        "Content-Type": "application/json",
        # "X-API-KEY": RPA_API_KEY,
    }

    try:
        response = requests.post(DJANGO_API_URL, data=json.dumps(payload), headers=headers, timeout=20)
        if response.status_code == 200:
            print(f"➜ API: Status da transferência {transferencia_id} enviado com sucesso.")
            return True
        else:
            print(
                f"✗ API ERRO ({response.status_code}): Falha ao enviar status para a transferência "
                f"{transferencia_id}. Resposta: {response.text}"
            )
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API ERRO: Impossível conectar ao servidor Django. Erro: {e}")
        return False
