from selenium.webdriver.common.by import By

from core.erp_core import BaseERP

class DesmancharItem(BaseERP):

    def executar(self):
        
        """
        Função principal do fluxo.
        """

        dep1_input='Almox Mont Carretas'
        dep2_input='Almox Serra'
        recurso='033316'
        qtd='-10,00'
        mp='110565'
        qt_mp='219,39'

        self.abrir_menu_1()

        self.clicar_menu('Estoque')
        self.esperar(1)

        self.clicar_menu('Transferência')
        self.esperar(1)
        self.abrir_menu_1()

        for i in range(10):

            self.abrir_menu_1()

            self.clicar_menu('Transferência simples de recursos')
            self.esperar(1.5)

            #Mudando visualização
            self.iframes()
            print("Mudando visualização")
            self.esperar(.5)
            self.clicar_v2(By.XPATH, '//*[@id="grdMovDepos"]//div[@id="changeViewButton"]', 5)
            self.esperar(.5)

            #Clicando em add
            print("Clicando em add")
            self.esperar(.5)
            self.clicar_v2(By.XPATH, '//*[@id="grdMovDepos"]//div[@id="insertButton"]', 5)
            self.esperar(.5)
        
            #Escrever classe
            self.escrever(By.XPATH,'//*[@id="grdMovDepos"]//input[@name="CLASSE"]','Movimentação de Depósito')
            self.esperar(.5)
            self.clicar_v2(By.XPATH,'//*[@id="1"]', 5)
            self.esperar(.5)
            self.clicar_v2(By.XPATH,'//*[@id="buttonsBar_grLookup"]/td[1]', 5)
            self.esperar(.5)

            #Escrever data de apontamento
            self.escrever(By.XPATH,'//*[@id="grdMovDepos"]//input[@name="MOVIMENTAC"]','29/11/2025')
            self.esperar(.5)

            # Escrever depósito
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="DEPOSITO"]', dep1_input)
            self.esperar(.5)

            #Escrever recurso
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="RECURSO"]', recurso)
            self.esperar(.5)

            # #Escrever pessoa
            # self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="PESSOA"]', '4357')
            # self.esperar(.5)

            #Escrevendo quantidade        
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="QUANTIDADE"]', qtd)
            self.esperar(1.5)

            #Buscando custo mat
            custo_mat = self.buscar_valor(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="CUSTOMAT"]')
            self.esperar(.5)
            #Tratando custo mat
            custo_mat = custo_mat.replace("-","")

            #Clicando em confirmar
            self.clicar_v2(By.XPATH, '//*[@id="grdMovDepos"]//div[@id="postButton"]')
            self.esperar(.5)
            #Verifica se mostra algum erro
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                continue
            self.esperar(.5)

            #Clicando em add na segunda linha
            self.clicar_v2(By.XPATH, '//*[@id="grdMovDepos"]//div[@id="insertButton"]')
            self.esperar(.5)

            # #Escrever classe
            # self.escrever(By.XPATH,'//*[@id="grdMovDepos"]//input[@name="CLASSE"]','Movimentação de Depósito')
            # self.esperar(.5)
            # self.clicar_v2(By.XPATH,'//*[@id="1"]', 5)
            # self.esperar(.5)
            # self.clicar_v2(By.XPATH,'//*[@id="buttonsBar_grLookup"]/td[1]', 5)
            # self.esperar(.5)

            #Escrever data de apontamento
            # self.escrever(By.XPATH,'//*[@id="grdMovDepos"]//input[@name="MOVIMENTAC"]','29/11/2025')
            # self.esperar(.5)

            # Escrever depósito
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="DEPOSITO"]', dep2_input)
            self.esperar(.5)

            #Escrever mp
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="RECURSO"]', mp)
            self.esperar(.5)

            # #Escrever pessoa
            # self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="PESSOA"]', '4357')
            # self.esperar(.5)

            # #Escrevendo quantidade        
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="QUANTIDADE"]', qt_mp)
            self.esperar(.5)

            #Escrevendo custo mat        
            self.escrever(By.XPATH, '//*[@id="grdMovDepos"]//input[@name="CUSTOMAT"]', custo_mat)
            self.esperar(.5)

            #Clicando em confirmar
            self.clicar_v2(By.XPATH, '//*[@id="grdMovDepos"]//div[@id="postButton"]')
            self.esperar(.5)
            #Verifica se mostra algum erro
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                continue
            self.esperar(.5)

            #Clicando em gravar
            self.clicar_v2(By.XPATH, "//p[contains(text(),'ravar')]/parent::span[contains(@class,'wf-button')]")
            self.esperar(.5)
            #Verifica se mostra algum erro
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                continue
            self.esperar(.5)

            self.sair_iframe()
            #Clicar em sim
            self.clicar_v2(By.ID, 'answers_0')
            #Verifica se mostra algum erro
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                continue
            self.esperar(.5)
            print("Aguardando alerta")
            alerta = self.obter_mensagem_alert()
            if alerta:
                print(f"[ALERTA] Apenas um alerta: {alerta}")
            self.esperar(.5)                

            print("Sucesso!!")

            self.fechar_aba_ate_fechar()

            self.esperar(10)


