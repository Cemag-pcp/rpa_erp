import os
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from bots.saldoAoVivo.flow import SaldoAoVivo
from core.db import get_erp_credentials_for_bot, get_headless_mode_for_bot

def main():

    name_bot = 'saldo_ao_vivo'

    # Verifica se o horário está entre 7 da manhã e 7 da noite
    agora = datetime.datetime.now().time()
    inicio = datetime.time(7, 0, 0)  # 7 da manhã
    fim = datetime.time(19, 0, 0)    # 7 da noite

    if not (inicio <= agora <= fim):
        return

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

    fluxo = SaldoAoVivo(driver)

    try:
        fluxo.abrir_url_140()
        # fluxo.abrir_url_testes()

        creds = get_erp_credentials_for_bot(name_bot)
        login = creds.get("erp_username")
        senha = creds.get("erp_password")

        fluxo.login(login, senha)
        fluxo.esperar(5)

        fluxo.executar()

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()

