import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from bots.transferirItem.transferencias import verificar_transferencias
from bots.transferirItem.flow import TransferirItem
from core.db import get_erp_credentials_for_bot, get_headless_mode_for_bot


def main():

    name_bot = 'transferir_item'

    while True:
    
        rows = verificar_transferencias()

        if rows:
            print(f"Encontradas {len(rows)} transferências a serem processadas.")

            headless = get_headless_mode_for_bot(name_bot)
            options = Options()
            if headless:
                options.add_argument("--headless=new")

            driver = webdriver.Chrome(options=options)

            # Registra o PID do chromedriver em arquivo para o gerenciador poder encerrar apenas este navegador
            pid_file = os.getenv("BOT_PID_FILE")
            try:
                service = getattr(driver, "service", None)
                process = getattr(service, "process", None) if service else None
                driver_pid = getattr(process, "pid", None) if process else None

                if pid_file and driver_pid is not None:
                    with open(pid_file, "w", encoding="utf-8") as f:
                        f.write(str(driver_pid))
            except Exception:
                # Se não conseguir registrar, apenas segue a execução normal
                pass

            fluxo = TransferirItem(driver)

            try:
                fluxo.abrir_url_140()
                # fluxo.abrir_url_testes()

                creds = get_erp_credentials_for_bot(name_bot)
                login = creds.get("erp_username")
                senha = creds.get("erp_password")

                fluxo.login(login, senha)
                fluxo.esperar(5)

                # abre menu
                fluxo.abrir_menu_1()

                fluxo.clicar_menu("Estoque")
                fluxo.clicar_menu("Transferência")

                # fecha menu
                fluxo.abrir_menu_1()

                fluxo.executar(rows)
            finally:
                try:
                    driver.quit()
                except Exception:
                    pass
        else:
            return "[INFO] Nenhuma transferência pendente encontrado."


if __name__ == "__main__":
    main()

