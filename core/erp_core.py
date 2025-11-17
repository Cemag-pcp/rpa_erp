import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.keys import Keys
import pandas as pd

class BaseERP:
    """
    Classe base para automações do ERP.  
    Todas as outras automações devem herdar desta classe.
    """

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    # =============================
    # UTILITÁRIOS GERAIS
    # =============================

    def esperar(self, segundos):
        """Pausa curta, útil após ações pesadas."""
        time.sleep(segundos)

    def clicar(self, by, value, timeout=None):
        if timeout is None:
            timeout = self.timeout

        try:
            elem = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            elem.click()
            self.esperar(3)
            
            return True

        except TimeoutException:
            print(f"[ERRO] Timeout ao tentar clicar: {value}")
            return False

        except ElementClickInterceptedException:
            print(f"[ERRO] Elemento interceptado ao clicar: {value}")
            return False

        except Exception as e:
            print(f"[FATAL] Erro inesperado ao clicar em {value}: {type(e).__name__} - {e}")
            return False
    
    def escrever(self, by, value, texto, limpar=True):
        try:
            elem = self.wait.until(EC.presence_of_element_located((by, value)))
            if limpar:
                elem.clear()
                self.esperar(1.5)
                print('[INFO] Limpando antes de escrever')
            elem.send_keys(texto)
            self.esperar(.5)
            elem.send_keys(Keys.TAB)
            print(f'[INFO] Escrito {value}')
            
            return True
        except TimeoutException:
            print(f"[ERRO] Não encontrou campo: {value}")
            
            return False

    # =============================
    # INICIALIZAR ERP
    # =============================

    def abrir_url_local(self):
        self.driver.get('http://127.0.0.1/sistema')

    def abrir_url_140(self):
        self.driver.get('http://192.168.3.140/sistema')

    def abrir_url_141(self):
        self.driver.get('http://192.168.3.141/sistema')

    def abrir_url_testes(self):
        self.driver.get('https://hcemag.innovaro.com.br/sistema/')

    # =============================
    # LOGIN
    # =============================

    def login(self, usuario, senha):
        self.escrever(By.ID, "username", usuario)
        self.escrever(By.ID, "password", senha)
        self.driver.find_element(By.ID, "password").send_keys(Keys.ENTER)

    # =============================
    # MENU
    # =============================

    def abrir_menu_1(self):
        
        """
        Função para abrir ou fechar menu no innovaro do tipo 1
        :nav: webdriver
        """

        self.clicar(By.CLASS_NAME, 'menuBar-button-label', 999)

    def abrir_menu_2(self):
        
        """
        Função para abrir ou fechar menu no innovaro do tipo 2
        :nav: webdriver
        """        

        self.clicar(By.XPATH, '//*[@id="bt_1898143037"]/table/tbody/tr/td[2]', 999)

    def tentar_abrir_2_menu(self):
        """
        Tenta abrir o menu do Innovaro automaticamente.
        - Primeiro tenta o tipo 1
        - Se não conseguir, tenta o tipo 2

        Retorna:
            1 -> se conseguiu abrir o menu tipo 1
            2 -> se conseguiu abrir o menu tipo 2
            None -> se nenhum dos dois funcionou
        """
        
        self.driver.switch_to.default_content()

        if self.abrir_menu_1():
            print("[INFO] Menu Innovaro tipo 1 aberto.")
            return 1

        if self.abrir_menu_2():
            print("[INFO] Menu Innovaro tipo 2 aberto.")
            return 2

        print("[ERRO] Nenhum menu do Innovaro foi encontrado.")
        return None

    def listar_itens_menu(self, classe):

        try:

            lista_menu = self.driver.find_elements(By.CLASS_NAME, classe)

            elementos_menu = []

            for x in range(len(lista_menu)):
                a = lista_menu[x].text
                elementos_menu.append(a)

            test_lista = pd.DataFrame(elementos_menu)
            test_lista = test_lista.loc[test_lista[0] != ""].reset_index()

            print(f"[INFO] Listou as opções do menu")
            self.esperar(.5)

        except Exception as e:
            print(f"[ERRO] Ocorreu um erro durante a listagem de opções: {e}")

        return (lista_menu, test_lista)

    def navegar_menu(self, *caminho):
        for item in caminho:
            if not self.clicar_no_menu(item):
                print(f"[ERRO] Falha ao acessar menu: {item}")
                return False
            self.esperar(1)
        return True
    
    def clicar_menu(self, item_menu):

        try:
            #Clicando em estoque
            lista_menu, test_list = self.listar_itens_menu('webguiTreeNodeLabel')
            self.esperar(1.5)
            click_producao = test_list.loc[test_list[0] == item_menu].reset_index(drop=True)['index'][0]
            lista_menu[click_producao].click()
            self.esperar(.5)

            print(f"[INFO] Clicado em {item_menu}")

            return True
        except ValueError as e:
            print(f"[ERRO] Não encontrado {item_menu}: {e}")

    # =============================
    # CONTROLE DE ABAS
    # =============================

    def fechar_aba_ate_fechar(self, max_tentativas=5):
        """
        Tenta fechar a aba atual repetidamente até realmente fechar.
        Retorna True se fechou, False se desistiu.
        """

        for tentativa in range(1, max_tentativas + 1):
            print(f"[INFO] Tentando fechar aba (tentativa {tentativa}/{max_tentativas})")

            try:
                # Tenta clicar no botão de fechar
                btn_fechar = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//span[contains(@onclick, 'Environment.getInstance().closeTab')]/div"
                    ))
                )
                btn_fechar.click()
                self.esperar(0.5)

            except Exception as e:
                print(f"[WARN] Não conseguiu clicar no botão de fechar: {e}")

            # Agora verifica se ainda existe uma aba aberta
            if not self.existe_aba_aberta(timeout=1):
                print("[OK] Aba fechada com sucesso!")
                return True

            self.esperar(0.5)

        print("[ERRO] Não foi possível fechar a aba após várias tentativas.")
        return False

    def existe_aba_aberta(self, timeout):
        """
        Verifica se existe pelo menos uma aba aberta no Innovaro.
        Considera qualquer elemento com class 'process-tab-label' dentro de #tabs.

        Retorna:
            True  -> se encontrou alguma aba
            False -> se não encontrou nenhuma
        """
        try:
            # espera até aparecer pelo menos uma aba, dentro do tempo
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#tabs .process-tab-label")
                )
            )
            return True
        except TimeoutException:
            return False

    def fechar_todas_as_abas(self):
        while self.existe_aba_aberta(timeout=1):
            self.fechar_aba_ate_fechar()

    # =============================
    # AÇÕES COMUNS DO ERP
    # =============================

    def iframes(self):

        iframe_list = self.driver.find_elements(By.CLASS_NAME, 'tab-frame')

        for iframe in range(len(iframe_list)):
            self.esperar(1)
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(iframe_list[iframe])
            except:
                pass
                
        return '[INFO] Entrando no iframe'

    def sair_iframe(self):

        self.driver.switch_to.default_content()

        return '[INFO] Saindo do iframe'
    
    def obter_mensagem_erro(self, timeout=5, fechar_apos_ler=True):
        """
        Captura a mensagem da janela de erro (errorMessageBox).

        Retorna:
            - string com a mensagem de erro, ex: "Não encontrou ocorrência para a pesquisa."
            - None, se não aparecer mensagem de erro dentro do timeout.
        """

        try:
            # Espera o container de erro ficar visível
            box = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "errorMessageBox"))
            )

            # Dentro do box, pega o texto da div.dialog-content > div
            msg_elem = box.find_element(By.CSS_SELECTOR, ".dialog-content div")
            mensagem = msg_elem.text.strip()

            print(f"[ERRO] Mensagem de erro capturada: {mensagem}")

            # Opcional: clicar no OK para fechar
            if fechar_apos_ler:
                try:
                    btn_ok = box.find_element(By.ID, "confirm")
                    btn_ok.click()
                except Exception as e:
                    print(f"[WARN] Não consegui clicar em OK do erro: {e}")

            return mensagem

        except TimeoutException:
            # Não apareceu mensagem de erro dentro do tempo definido
            return None

    def obter_mensagem_alert(self, timeout=5, fechar_apos_ler=True):
        """
        Captura a mensagem da janela de alerta (alertMessageBox).

        Retorna:
            - string com a mensagem de alerta, ex: "Requisição aprovada com sucesso!"
            - None, se não aparecer mensagem de alerta dentro do timeout.
        """

        try:
            # Espera o container de alerta ficar visível
            box = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.ID, "alertMessageBox"))
            )

            # Dentro do box, pega o texto da div.dialog-content > div
            msg_elem = box.find_element(By.CSS_SELECTOR, ".dialog-content div")
            mensagem = msg_elem.text.strip()

            print(f"[ALERTA] Mensagem de alerta capturada: {mensagem}")

            # Opcional: clicar no OK para fechar
            if fechar_apos_ler:
                try:
                    btn_ok = box.find_element(By.ID, "confirm")
                    btn_ok.click()
                except Exception as e:
                    print(f"[WARN] Não consegui clicar em OK do alerta: {e}")

            return mensagem

        except TimeoutException:
            # Não apareceu mensagem de alerta dentro do tempo definido
            return None
