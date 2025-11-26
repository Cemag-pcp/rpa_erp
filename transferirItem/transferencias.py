import psycopg2
from psycopg2.extras import DictCursor  # Para retornar resultados como dicionários
import os
import requests
import json

def verificar_transferencias():
    
    try:
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            dbname='postgres',  
            user='postgres',      
            password='15512332',    
            host='database-1.cdcogkfzajf0.us-east-1.rds.amazonaws.com',  
            port='5432'              
        )

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
            WHERE st.data_entrega IS NOT NULL AND (st.rpa IS NULL OR st.rpa != 'OK')
        """

        cursor.execute(query)
        rows = cursor.fetchall()
        return rows

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados ou executar a consulta: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def enviar_status_via_api(transferencia_id, status, dep_destino, rec, qtd, observacao):
    """
    Envia o status de uma requisição para a API do Django.
    """
    # --- Configuração da API ---
    DJANGO_API_URL = 'https://apontamentousinagem.onrender.com/core/api/rpa/update-transfer/' 
    RPA_API_KEY = 'dfjf6348964jgjdofj58690yfndjwe395igjd032054kghbdpgçblej389503k2quf78rj5iy90gkmnj4u8rjfksk'  
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
        "X-API-KEY": RPA_API_KEY,
    }

    try:
        response = requests.post(DJANGO_API_URL, data=json.dumps(payload), headers=headers, timeout=20)
        if response.status_code == 200:
            print(f"? API: Status da requisição {transferencia_id} enviado com sucesso.")
            return True
        else:
            print(f"? API ERRO ({response.status_code}): Falha ao enviar status para a requisição {transferencia_id}. Resposta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"? API ERRO: Impossível conectar ao servidor Django. Erro: {e}")
        return False
