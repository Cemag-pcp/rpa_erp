from selenium.webdriver.common.by import By

from core.erp_core import BaseERP
from requisitarItem.requisicoes import enviar_status_via_api

import datetime


class RequisitarItem(BaseERP):

    def executar(self, rows):
        
        """
        Função principal do fluxo.
        """

        # Loop infinito para realizar as requsições
        for row in rows:
            id = row[0]
            rec = row[7]
            qtd = row[1]
            tipo_requisicao = row[4]
            requisitante_matricula = row[6]
            ccusto_text = row[5]
            observacao_text = row[2] if row[2] else ' '

            print('-------------------------------------------------------')
            print(f"[INFO] Indo para item {rec}\nRequisitado por: {requisitante_matricula}\nRequisitado no dia: {row[3]}")

            self.fechar_aba_ate_fechar()

            self.esperar(.5)
            self.abrir_menu_2()

            self.esperar(.5)
            self.clicar_menu('Requisições')

            self.esperar(.5)
            
            self.iframes()

            #Mudando visualização
            print("Mudando visualização")
            self.esperar(.5)
            self.clicar_v2(By.XPATH, '//*[@id="grdRequisicoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)

            #Clicando em insert
            print("Clicando em insert")
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[2]', 5)
            self.esperar(.5)

            #Inputando classe
            print("Escrevendo classe")
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[1]/td[4]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[1]/td[4]/table/tbody/tr/td[1]/input', tipo_requisicao)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[1]/td[4]/table/tbody/tr/td[1]/input', tipo_requisicao)
            self.esperar(.5)

            #Inputando requisitante
            print("Escrevendo requisitante")
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', requisitante_matricula)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', requisitante_matricula)
            self.esperar(.5)

            #Aguardar erro
            print("Aguardando erro")
            self.sair_iframe()
            self.esperar(.5)
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(id,erro,tipo_requisicao)
                continue
            self.esperar(.5)

            #Inputando ccusto
            print("Escrevendo ccusto")
            self.iframes()
            self.clicar_v2(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[4]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[4]/table/tbody/tr/td[1]/input', ccusto_text)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[3]/td[4]/table/tbody/tr/td[1]/input', ccusto_text)
            self.esperar(.5)

            #Aguardar erro
            print("Aguardando erro")
            self.sair_iframe()
            self.esperar(.5)
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(id,erro,tipo_requisicao)
                continue
            self.esperar(.5)

            #Inputando recurso
            print("Escrevendo recurso")
            self.iframes()
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', rec)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', rec)
            self.esperar(.5)

            #Aguardar erro
            print("Aguardando erro")
            self.sair_iframe()
            self.esperar(.5)
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(id,erro,tipo_requisicao)
                continue
            self.esperar(.5)

            #Inputando quantidade
            print("Escrevendo quantidade")
            self.iframes()
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[7]/td[3]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[7]/td[3]/table/tbody/tr/td[1]/input', qtd)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[7]/td[3]/table/tbody/tr/td[1]/input', qtd)
            self.esperar(.5)

            #inputando Observação
            print("Escrevendo observação")
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[9]/td[2]/table/tbody/tr/td[1]/textarea', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[9]/td[2]/table/tbody/tr/td[1]/textarea', observacao_text)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[1]/td/table/tbody/tr[9]/td[2]/table/tbody/tr/td[1]/textarea', observacao_text)
            self.esperar(.5)

            #Clicando em confirmar (insert)
            print("Clicando em insert")
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[4]', 5)
            self.esperar(.5)

            # mudar visualização
            print("Mudando visualização")
            self.clicar_v2(By.XPATH, '//*[@id="grdRequisicoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(1.5)
            
            # selecionando checkbox
            print("Selecionando checkbox")
            self.clicar_v2(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[1]/td[1]/table/tbody/tr[4]/td[1]', 5)
            self.esperar(.5)

            # clicando em aprovar
            print("Clicando em aprovar")
            self.clicar_v2(By.XPATH, '//*[@id="buttonsBar_grdRequisicoes"]/td[1]', 5)
            self.esperar(.5)

            #Aguardar erro
            print("Aguardando erro")
            self.sair_iframe()
            self.esperar(.5)
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(id,erro,tipo_requisicao)
                continue
            self.esperar(.5)

            print("Aguardando alerta")
            alerta = self.obter_mensagem_alert()
            if alerta:
                print(f"[ALERTA] Apenas um alerta: {alerta}")
            self.esperar(.5)                

            # clicando em baixar
            print("Clicando em baixar")
            self.iframes()
            self.clicar_v2(By.XPATH,'//*[@id="buttonsBar_grdRequisicoes"]/td[3]', 5)
            self.esperar(.5)

            # preenchendo classe movimentação de depósito
            print("Escrevendo classe movimentação de depósito")
            self.clicar_v2(By.XPATH,'//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/table/tbody/tr/td[1]/input', 'Movimentação de depósitos')
            self.esperar(.5)
            # self.verificar_se_escreveu(By.XPATH, '//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/table/tbody/tr/td[1]/input', 'Movimentação de depósitos')
            self.esperar(.5)
            self.clicar_v2(By.XPATH,'//*[@id="1"]', 5)
            self.esperar(.5)
            self.clicar_v2(By.XPATH,'//*[@id="buttonsBar_grLookup"]/td[1]', 5)
            self.esperar(.5)

            # Preenchendo depósito
            print("Escrevendo depósito")
            self.clicar_v2(By.XPATH,'//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input', 'central')
            self.esperar(.5)

            # Preenchendo data de movimentação
            print("Escrevendo data de movimentação")
            self.clicar_v2(By.XPATH,'//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', datetime.datetime.now().date().strftime('%d/%m/%Y'))
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="grdInfoBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[5]/td[2]/table/tbody/tr/td[1]/input', datetime.datetime.now().date().strftime('%d/%m/%Y'))
            self.esperar(.5)

            # clicando em confirmar baixa
            print("Clicando em confirmar baixa")
            self.sair_iframe()
            self.esperar(.5)
            self.clicar_v2(By.XPATH,'/html/body/div[4]/div/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)

            self.iframes()
            self.esperar(.5)

            # clicar em confirmar    
            print("Confirmando em confirmar")
            self.clicar_v2(By.XPATH,'//*[@id="grdRequisicoes"]/tbody/tr[1]/td[1]/table/tbody/tr[10]/td[7]/div', 5)
            self.esperar(.5)

            # clicando em gravar
            print("Clicando em gravar")
            self.sair_iframe()
            self.clicar_v2(By.XPATH, '/html/body/div[4]/div/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[2]', 5)
            self.esperar(.5)

            # confirmar_gravacao
            print("Clicando em confirmar gravação")
            self.clicar_v2(By.XPATH, '//*[@id="answers_0"]', 5)
            self.esperar(.5)

            print("Aguardando erro")
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.esperar(.5)
                self.fechar_aba_ate_fechar()
                # devolve erro pro banco
                enviar_status_via_api(id,erro,tipo_requisicao)
                continue
            self.esperar(.5)

            print("Aguardando alerta")
            alerta = self.obter_mensagem_alert()
            if alerta:
                print(f"[ALERTA] Apenas um alerta: {alerta}")
                enviar_status_via_api(id,'OK',tipo_requisicao)
                # devolve sucesso pro banco
            self.esperar(.5)                
