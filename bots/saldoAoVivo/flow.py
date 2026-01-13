from selenium.webdriver.common.by import By

from core.erp_core import BaseERP
from .saldo_ao_vivo import inserir_gspread_saldo_central_mp, apagar_ultimo_download, inserir_gspread_saldo_levantamento, inserir_gspread_saldo_levantamento_incluindo_em_processo,inserir_postgres_saldo_levantamento

import datetime

class SaldoAoVivo(BaseERP):

    def executar(self):
        
        """
        Função principal do fluxo.
        """
        
        # abre menu
        self.abrir_menu_1()

        self.clicar_menu("Estoque")
        self.clicar_menu("Consultas")
        self.clicar_menu("Saldos de Recursos - CEMAG")
        self.esperar(2)

        # inputando data
        self.iframes()
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', 'h')
        self.esperar(.5)

        # Inputando o depósito
        self.escrever(By.XPATH, '//*[@id="vars"]/tbody/tr[1]/td[1]/table/tbody/tr[8]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', 'Almox Central')
        self.esperar(.5)

        # Limpar campo de recursos
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[10]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', '')
        self.esperar(.5)

        # Inserir agrupamentos central mp
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[20]/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', 'Etapa')
        self.esperar(.5)

        # Inserir agrupamentos almox
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[20]/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', 'Classe de Recursos')
        self.esperar(.5)

        # exportar primeira tela
        self.clicar_v2(By.XPATH, '/html/body/div[4]/div/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[2]/span[2]', 5)
        self.aguardando_desaparecer_item(By.XPATH, '//*[@id="content_statusMessageBox"]')
        
        # exportar segunda tela
        self.clicar_v2(By.XPATH, "//span[@class='wf-button default' and contains(., 'Exportar')]", 5)
        self.esperar(.5)
        
        # escolher opção de excel
        self.clicar_v2(By.XPATH, "/html/body/div[8]/table/tbody/tr/td[2]/div/div/div[2]", 5)
        self.esperar(.5)

        # executar
        self.clicar_v2(By.XPATH, "/html/body/div[4]/div[2]/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]/span[2]", 5)
        self.esperar(.5)
        #### TALVEZ SERÁ NECESSÁRIO ADICIONAR UM TEMPORIZADOR NESSA ETAPA, POIS DEMORA UM POUCO PARA CARREGAR O LOADING

        # clique aqui para fazer download do arquivo
        self.iframes()
        self.clicar_v2(By.XPATH, "/html/body/span", 5)
        self.esperar(10)

        # Inserir no google sheets
        inserir_gspread_saldo_central_mp()
        self.esperar(1)

        # inserir no pgsql        
        inserir_postgres_saldo_levantamento()
        self.esperar(1)

        # fechar abas
        self.sair_iframe()
        self.fechar_aba_ate_fechar()

        # apagar último arquivo
        apagar_ultimo_download()

        # Ir para saldo de recurso MP
        self.abrir_menu_1()
        self.clicar_menu("Saldos de Recursos - CEMAG")

        print("Indo para saldo levantamento")

        # Inputando o depósito
        self.iframes()
        self.escrever(By.XPATH, '//*[@id="vars"]/tbody/tr[1]/td[1]/table/tbody/tr[8]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', '')
        self.esperar(.5)

        # Limpar campo de recursos
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[10]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', '')
        self.esperar(.5)

        # Apagar mat prima
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[10]/td/table/tbody/tr[15]/td[2]/table/tbody/tr/td[1]/input', '')
        self.esperar(.5)

        # Campo de agrupamento
        self.escrever(By.XPATH, '/html/body/div[2]/form/table/tbody/tr[1]/td[1]/table/tbody/tr[20]/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', 'Etapa')
        self.esperar(.5)

        # exportar primeira tela
        self.clicar_v2(By.XPATH, '/html/body/div[4]/div/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[2]/span[2]', 5)
        self.aguardando_desaparecer_item(By.XPATH, '//*[@id="content_statusMessageBox"]')
        
        # exportar segunda tela
        self.clicar_v2(By.XPATH, "//span[@class='wf-button default' and contains(., 'Exportar')]", 5)
        self.esperar(.5)
        
        # escolher opção de excel
        self.clicar_v2(By.XPATH, "/html/body/div[8]/table/tbody/tr/td[2]/div/div/div[2]", 5)
        self.esperar(.5)

        # executar
        self.clicar_v2(By.XPATH, "/html/body/div[4]/div[2]/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]/span[2]", 5)
        self.esperar(.5)
        #### TALVEZ SERÁ NECESSÁRIO ADICIONAR UM TEMPORIZADOR NESSA ETAPA, POIS DEMORA UM POUCO PARA CARREGAR O LOADING

        # clique aqui para fazer download do arquivo
        self.iframes()
        self.clicar_v2(By.XPATH, "/html/body/span", 5)
        self.esperar(10)

        # Inserir no google sheets
        inserir_gspread_saldo_levantamento()
        self.esperar(1)
        inserir_gspread_saldo_levantamento_incluindo_em_processo()
        self.esperar(1)
        apagar_ultimo_download()

        # fechar abas
        self.sair_iframe()
        self.fechar_aba_ate_fechar()