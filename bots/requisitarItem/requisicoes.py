import os
import json
import requests
from psycopg2.extras import DictCursor  # Para retornar resultados como dicionários
from dotenv import load_dotenv

from core.db import get_db_connection

load_dotenv()

def verificar_requisicoes():
    try:
        # Conectar ao banco de dados PostgreSQL usando configuração do .env
        conn = get_db_connection()

        cursor = conn.cursor(cursor_factory=DictCursor)  # Usa DictCursor para obter resultados como dicionários

        # Executar a consulta com junção
        query = """
            SELECT
                sr.id,
                sr.quantidade,
                sr.obs,
                sr.data_solicitacao,
                cac.nome as classe_requisicao,
                cc1.codigo AS cc_nome,
                f.matricula AS funcionario_nome,
                i.codigo AS item_nome,
                sr.data_entrega,
                sr.rpa
            FROM
                apontamento_v2.solicitacao_almox_solicitacaorequisicao sr
            JOIN
                apontamento_v2.cadastro_almox_cc cc1 ON sr.cc_id = cc1.id
            LEFT JOIN
                apontamento_v2.cadastro_almox_classerequisicao cac ON sr.classe_requisicao_id = cac.id
            LEFT JOIN
                apontamento_v2.cadastro_almox_funcionario f ON sr.funcionario_id = f.id
            LEFT JOIN
                apontamento_v2.cadastro_almox_itenssolicitacao i ON sr.item_id = i.id
            WHERE
                sr.data_entrega IS NOT NULL
                AND (sr.rpa IS NULL OR sr.rpa != 'OK')
                -- AND data_solicitacao >= date_trunc('month', CURRENT_DATE)
            ORDER BY
                sr.data_solicitacao;
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


def enviar_status_via_api(requisicao_id, status, tipo_requisicao, chave=None):
    """
    Envia o status de uma requisição para a API do Django.
    """
    # --- Configuração da API ---
    DJANGO_API_URL = "https://apontamentousinagem.onrender.com/core/api/rpa/update-status/"
    # RPA_API_KEY = os.getenv("RPA_API_KEY", "dfjf6348964jgjdofj58690yfndjwe395igjd032054kghbdpgçblej389503k2quf78rj5iy90gkmnj4u8rjfksk")
    # ---------------------------

    payload = {
        "id": requisicao_id,
        "status": status,
        "tipo_requisicao": tipo_requisicao,
        "chave": chave
    }
    # headers = {
    #     "Content-Type": "application/json",
    #     "X-API-KEY": RPA_API_KEY,
    # }

    try:
        response = requests.post(DJANGO_API_URL, data=json.dumps(payload), timeout=20)
        if response.status_code == 200:
            print(f"➜ API: Status da requisição {requisicao_id} enviado com sucesso.")
            return True
        else:
            print(
                f"✗ API ERRO ({response.status_code}): Falha ao enviar status para a requisição "
                f"{requisicao_id}. Resposta: {response.text}"
            )
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API ERRO: Impossível conectar ao servidor Django. Erro: {e}")
        return False
