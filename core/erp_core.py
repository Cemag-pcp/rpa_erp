import os
import time
import logging
import functools
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

# =============================
# 1. CONFIGURAÇÃO DE LOGS
# =============================
def configurar_logger():
    """
    Configura o logger para salvar em arquivo e mostrar no console.
    """
    logger = logging.getLogger("ERP_Automacao")
    logger.setLevel(logging.INFO)

    # Evita duplicidade de logs se reinicializar
    if not logger.handlers:
        # Formato: [DATA HORA] [NIVEL] - MENSAGEM
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # Handler Arquivo (salva o histórico)
        file_handler = logging.FileHandler('execucao_erp.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler Console (mostra na tela em tempo real)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Instância global do logger para ser usada no arquivo
log = configurar_logger()

# =============================
# 2. DECORATOR PARA RASTREAR PASSOS
# =============================
def log_passo(func):
    """
    Decorator que loga automaticamente o início, fim e erros de cada função.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nome_funcao = func.__name__
        try:
            # Log antes de executar
            # args[0] é o 'self', ignoramos para limpar o log
            log.info(f"Iniciando passo: {nome_funcao}")
            
            resultado = func(*args, **kwargs)
            
            # Log após sucesso
            log.info(f"Passo concluído: {nome_funcao}")
            return resultado

        except Exception as e:
            # Log de erro com traceback se quebrar
            log.error(f"Falha no passo {nome_funcao}. Erro: {str(e)}", exc_info=True)
            raise e # Relança o erro para o script principal tratar se necessário
    return wrapper

class BaseERP:
    """
    Classe base para automações do ERP.  
    Todas as outras automações devem herdar desta classe.
    """

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout
        log.info("Instância BaseERP iniciada.")
    # =============================
    # UTILITÁRIOS GERAIS
    # =============================

    def esperar(self, segundos):
        """Pausa curta, útil após ações pesadas."""
        time.sleep(segundos)
    
    @log_passo
    def clicar_v1(self, by, value, timeout=None):
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
            log.warning(f"Timeout ao tentar clicar: {value}")
            return False

        except ElementClickInterceptedException:
            log.warning(f"Elemento interceptado ao clicar: {value}")
            return False

        except Exception as e:
            log.critical(f"Erro inesperado ao clicar em {value}: {type(e).__name__} - {e}")
            return False

    @log_passo
    def clicar_v2(self, by, value, tentativas=20):

        for tentativa in range(tentativas):

            try:
                # Sempre volta para o conteúdo principal
                self.driver.switch_to.default_content()

                # tenta clicar no contexto principal
                elem = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((by, value))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                elem.click()
                log.info(f"Clique realizado em {value} na tentativa {tentativa+1}")
                return True

            except:
                pass

            # Se falhou, tentar nos iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for idx, frame in enumerate(iframes):

                try:
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(frame)

                    elem = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((by, value))
                    )

                    self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)

                    try:
                        elem.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", elem)

                    log.info(f"Clique realizado em {value} dentro do iframe {idx}")
                    return True

                except:
                    continue

            log.debug(f"Tentativa {tentativa+1}/{tentativas} falhou. Tentando novamente...")

            self.esperar(1)

        log.error(f"Não foi possível clicar em {value} após {tentativas} tentativas.")
        return False
    
    @log_passo
    def escrever(self, by, value, texto, limpar=True):
        try:
            elem = self.wait.until(EC.presence_of_element_located((by, value)))
            if limpar:
                elem.clear()
                self.esperar(1.5)
                log.debug('Limpando antes de escrever')
            elem.send_keys(texto)
            self.esperar(.5)
            elem.send_keys(Keys.TAB)
            log.info(f'Escrito: {texto} em {value}')
            
            return True
        except TimeoutException:
            log.error(f"Não encontrou campo para escrever: {value}")
            
            return False
    
    @log_passo
    def verificar_se_escreveu(self, by, value, texto, limpar=True, tentativas=2):
        """
        Verifica se o input está preenchido.
        - Se já estiver preenchido: só loga e retorna True.
        - Se estiver vazio: escreve `texto`, verifica se preencheu.
        - Se após escrever continuar vazio, tenta novamente até 'tentativas' vezes.

        by: tipo de seletor (By.ID, By.XPATH, etc.)
        value: valor do seletor
        texto: texto que será escrito caso o campo esteja vazio
        limpar: se True, dá .clear() antes de escrever
        tentativas: número máximo de tentativas de escrita/verificação

        Retorna:
            True  -> se o campo estiver ou ficar preenchido
            False -> se não conseguir preencher
        """
        try:
            elem = self.wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            log.error(f"Não encontrou campo: {value}")
            return False

        for tentativa in range(1, tentativas + 1):
            # 1) Verifica se já está preenchido
            valor_atual = (elem.get_attribute("value") or "").strip()

            if valor_atual:
                log.info(f"Campo {value} já preenchido: '{valor_atual}'")
                return True

            # 2) Se estiver vazio, tenta escrever
            log.info(f"Campo {value} vazio. Tentando escrever (tentativa {tentativa}/{tentativas})...")     

            if limpar:
                elem.clear()
                self.esperar(0.5)
                print("[INFO] Limpando campo antes de escrever")

            elem.send_keys(texto)
            self.esperar(0.5)
            elem.send_keys(Keys.TAB)
            self.esperar(0.5)

            # 3) Verifica novamente após escrever
            valor_atual = (elem.get_attribute("value") or "").strip()

            if valor_atual:
                log.info(f"Campo {value} preenchido com sucesso: '{valor_atual}'")
                return True
            else:
                log.warning(f"Campo {value} ainda vazio após tentativa {tentativa}")

        log.error(f"Falha ao preencher campo {value} após {tentativas} tentativas.")
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

        self.clicar_v1(By.CLASS_NAME, 'menuBar-button-label', 999)

    def abrir_menu_2(self):
        
        """
        Função para abrir ou fechar menu no innovaro do tipo 2
        :nav: webdriver
        """        

        self.clicar_v1(By.XPATH, '//*[@id="bt_1898143037"]/table/tbody/tr/td[2]', 999)

    @log_passo
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
            log.info("Menu Innovaro tipo 1 aberto.")
            return 1

        if self.abrir_menu_2():
            log.info("Menu Innovaro tipo 2 aberto.")
            return 2

        log.error("Nenhum menu do Innovaro foi encontrado.")
        return None

    @log_passo
    def listar_itens_menu(self, classe):

        try:

            self.sair_iframe()

            lista_menu = self.driver.find_elements(By.CLASS_NAME, classe)

            elementos_menu = []

            for x in range(len(lista_menu)):
                a = lista_menu[x].text
                elementos_menu.append(a)

            test_lista = pd.DataFrame(elementos_menu)
            test_lista = test_lista.loc[test_lista[0] != ""].reset_index()

            log.info("Listou as opções do menu")
            self.esperar(.5)

        except Exception as e:
            log.error(f"Ocorreu um erro durante a listagem de opções: {e}")

        return (lista_menu, test_lista)
    
    @log_passo
    def clicar_menu(self, item_menu):

        try:
            #Clicando em estoque
            lista_menu, test_list = self.listar_itens_menu('webguiTreeNodeLabel')
            self.esperar(1.5)
            click_producao = test_list.loc[test_list[0] == item_menu].reset_index(drop=True)['index'][0]
            lista_menu[click_producao].click()
            self.esperar(1.5)

            log.info(f"Clicado em {item_menu}")

            return True
        except ValueError as e:
            log.error(f"Não encontrado {item_menu}: {e}")

    # =============================
    # CONTROLE DE ABAS
    # =============================
    
    @log_passo
    def fechar_aba_ate_fechar(self, max_tentativas=5):
        """
        Tenta fechar a aba atual repetidamente até realmente fechar.
        Retorna True se fechou, False se desistiu.
        """

        for tentativa in range(1, max_tentativas + 1):
            log.info(f"Tentando fechar aba (tentativa {tentativa}/{max_tentativas})")

            try:
                # Tenta clicar no botão de fechar
                btn_fechar = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//span[contains(@onclick, 'Environment.getInstance().closeTab')]/div"
                    ))
                )
                self.esperar(0.5)
                btn_fechar.click()

            except Exception as e:
                log.error(f"Não conseguiu clicar no botão de fechar: {e}")

            # Agora verifica se ainda existe uma aba aberta
            if not self.existe_aba_aberta(timeout=1):
                log.info("Nenhuma aba aberta")
                return True

            self.esperar(0.5)

        log.error("Não foi possível fechar a aba após várias tentativas.")
        return False

    @log_passo
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

    @log_passo
    def fechar_todas_as_abas(self):
        while self.existe_aba_aberta(timeout=1):
            self.fechar_aba_ate_fechar()

    # =============================
    # AÇÕES COMUNS DO ERP
    # =============================

    @log_passo
    def iframes(self):

        iframe_list = self.driver.find_elements(By.CLASS_NAME, 'tab-frame')

        for iframe in range(len(iframe_list)):
            self.esperar(1)
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(iframe_list[iframe])
            except:
                pass
                
        return log.info('Entrando no iframe')
    
    @log_passo
    def sair_iframe(self):

        self.driver.switch_to.default_content()

        return log.info('Saindo do iframe')
    
    @log_passo
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

            log.info(f"Mensagem de erro capturada: {mensagem}")

            # Opcional: clicar no OK para fechar
            if fechar_apos_ler:
                try:
                    btn_ok = box.find_element(By.ID, "confirm")
                    btn_ok.click()
                except Exception as e:
                    log.error(f"Não consegui clicar em OK do erro: {e}")

            return mensagem + " - " + datetime.now().strftime("%d/%m/%Y %H:%M")

        except TimeoutException:
            # Não apareceu mensagem de erro dentro do tempo definido
            log.info(f"Não mostrou nenhuma mensagem de erro")
            return None
    
    @log_passo
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

            log.info(f"Mensagem de alerta capturada: {mensagem}")

            # Opcional: clicar no OK para fechar
            if fechar_apos_ler:
                try:
                    btn_ok = box.find_element(By.ID, "confirm")
                    btn_ok.click()
                except Exception as e:
                    log.error(f"Não consegui clicar em OK do alerta: {e}")

            return mensagem

        except TimeoutException:
            # Não apareceu mensagem de alerta dentro do tempo definido
            log.info("Não apareceu mensagem de alerta dentro do tempo definido")
            return None


    def aguardando_aparecer_item(self, by, value):

        log.info("Aguardando modal para confimar")

        self.sair_iframe()
        # Carregando até aparecer o MODAL para CONFIRMAR
        while True:
            elements = self.driver.find_elements(by, value)
            if len(elements) >= 1:
                break
            else:
                log.info("Carregando...")
                self.esperar(1)  # Esperar 1 segundo antes de verificar novamente
        
        return log.info('Item na tela')