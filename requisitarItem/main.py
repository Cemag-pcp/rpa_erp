from selenium import webdriver
from selenium.webdriver.common.by import By

from requisitarItem.requisicoes import verificar_requisicoes
from requisitarItem.flow import RequisitarItem

def main():

    rows = verificar_requisicoes()
    
    if rows:
        print(f"Encontradas {len(rows)} requisições a serem processadas.")

        driver = webdriver.Chrome()

        # --- Configuração para rodar em mostrar a tela do chrome ---

        # options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")  # ou só "--headless" dependendo da versão
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # driver = webdriver.Chrome(options=options)

        # ---------------------------

        fluxo = RequisitarItem(driver)

        fluxo.abrir_url_140()
        fluxo.login("user_almox", "samuel05")
        fluxo.esperar(5)

        # abre menu
        fluxo.abrir_menu_2()
        
        fluxo.clicar_menu('Estoque')
        fluxo.clicar_menu('Requisição')

        # fecha menu
        fluxo.abrir_menu_2()

        fluxo.executar(rows)
        # fluxo.executar2()

    else:
        return "[INFO] Nenhuma requisição pendente encontrada."

if __name__ == "__main__":
    while True:
        main()
