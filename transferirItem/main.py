import os

from selenium import webdriver
from selenium.webdriver.common.by import By

from transferirItem.transferencias import verificar_transferencias
from transferirItem.flow import TransferirItem


def main():
    rows = verificar_transferencias()

    if rows:
        print(f"Encontradas {len(rows)} transferências a serem processadas.")

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

        fluxo = TransferirItem(driver)

        try:
            # fluxo.abrir_url_140()
            fluxo.abrir_url_testes()
            
            fluxo.login("luan araujo", "luanaraujo7")
            fluxo.esperar(5)

            # abre menu
            fluxo.abrir_menu_1()

            fluxo.clicar_menu("Estoque")
            fluxo.clicar_menu("Transferência")

            # fecha menu
            fluxo.abrir_menu_1()

            fluxo.executar(rows)
            # fluxo.executar2()
        finally:
            try:
                driver.quit()
            except Exception:
                pass
    else:
        return "[INFO] Nenhuma transferência pendente encontrada."


if __name__ == "__main__":
    while True:
        main()

