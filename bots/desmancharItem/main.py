import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from .flow import DesmancharItem
from core.db import get_erp_credentials_for_bot


def main():

    name_bot = 'bot_test_desmanche'

    driver = webdriver.Chrome()

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
    
    fluxo = DesmancharItem(driver)

    try:
        # fluxo.abrir_url_140()
        fluxo.abrir_url_testes()

        # creds = get_erp_credentials_for_bot(name_bot)
        # login = creds.get("erp_username")
        # senha = creds.get("erp_password")

        login = 'luan araujo'
        senha = 'luanaraujo7'

        fluxo.login(login, senha)
        fluxo.esperar(5)

        fluxo.executar()

        driver.quit()

    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()

