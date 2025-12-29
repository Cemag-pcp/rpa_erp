from selenium.webdriver.common.by import By

from core.erp_core import BaseERP
from bots.transferirItem.transferencias import enviar_status_via_api

import datetime

class TransferirItem(BaseERP):

    def executar(self, rows):
        
        """
        Função principal do fluxo.
        """

        # Loop infinito para realizar as requsições
        for row in rows:
            id = row[0]
            qtd = row[1]
            rec = row[5]
            dep_destino = row[6]
            observacao_text = row[8] if row[8] else ' '
            dep_origem = 'almox central'

            print('-------------------------------------------------------')
            print(f"[INFO] Indo para item {rec}\nDepósito destino: {dep_destino}\nRequisitado no dia: {row[3]}")

            self.fechar_aba_ate_fechar()

            self.esperar(.5)
            self.abrir_menu_1()

            self.esperar(.5)
            self.clicar_menu('Solicitação de transferência entre depósitos')

            self.esperar(.5)
            
            self.iframes()

            #Mudando visualização
            print("Mudando visualização")
            self.esperar(.5)
            self.clicar_v2(By.XPATH, '//*[@id="solicitacoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)

            #Clicando em insert
            print("Clicando em insert")
            self.clicar_v2(By.XPATH,'//*[@id="solicitacoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[2]', 5)
            self.esperar(.5)
            
            # Buscando chave
            print("Buscando chave da transferência")
            chave = self.buscar_valor(By.XPATH, '//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[3]/td[2]/table/tbody/tr/td[1]/input')
            self.esperar(.5)
            # apenas para debugar
            print(chave)

            #Inputando deposito origem
            print("Escrevendo deposito origem")
            self.clicar_v2(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[11]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[11]/td[2]/table/tbody/tr/td[1]/input', dep_origem)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[11]/td[2]/table/tbody/tr/td[1]/input', dep_origem)
            self.esperar(.5)

            #Inputando deposito destino
            print("Escrevendo deposito destino")
            self.clicar_v2(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[13]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[13]/td[2]/table/tbody/tr/td[1]/input', dep_destino)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[13]/td[2]/table/tbody/tr/td[1]/input', dep_destino)
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
                enviar_status_via_api(
                    transferencia_id=id,
                    status=erro,
                    dep_destino=dep_destino,
                    rec=rec,
                    qtd=qtd,
                    observacao=observacao_text
                )
                continue
            self.esperar(.5)

            #Inputando recurso
            print("Escrevendo recurso")
            self.iframes()
            self.clicar_v2(By.XPATH, '//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[15]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[15]/td[2]/table/tbody/tr/td[1]/input', rec)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[15]/td[2]/table/tbody/tr/td[1]/input', rec)
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
                enviar_status_via_api(
                    transferencia_id=id,
                    status=erro,
                    dep_destino=dep_destino,
                    rec=rec,
                    qtd=qtd,
                    observacao=observacao_text
                )
                continue
            self.esperar(.5)

            #Inputando quantidade
            print("Escrevendo quantidade")
            self.iframes()
            self.clicar_v2(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[25]/td[2]/table/tbody/tr/td[1]', 5)
            self.esperar(.5)
            self.escrever(By.XPATH,'//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[25]/td[2]/table/tbody/tr/td[1]/input', qtd)
            self.esperar(.5)
            self.verificar_se_escreveu(By.XPATH, '//*[@id="solicitacoes"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr[25]/td[2]/table/tbody/tr/td[1]/input', qtd)
            self.esperar(.5)

            #Aguardar erro
            print("Aguardando erro")
            self.sair_iframe()
            self.esperar(.5)
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(
                    transferencia_id=id,
                    status=erro,
                    dep_destino=dep_destino,
                    rec=rec,
                    qtd=qtd,
                    observacao=observacao_text
                )
                continue
            self.esperar(.5)

            #Clicando em confirmar (insert)
            print("Clicando em insert")
            self.clicar_v2(By.XPATH,'//*[@id="solicitacoes"]/thead/tr[1]/td[1]/table/tbody/tr/td[2]/table/tbody/tr/td[4]', 5)
            self.esperar(.5)

            # clicando em aprovar
            print('clicando em aprovar')
            self.clicar_v2(By.XPATH, '//*[@id="buttonsBar_solicitacoes"]/td[1]', 5)
            
            print("Aguardando modal para confirmar")
            self.aguardando_aparecer_item(By.XPATH, '//*[@id="confirm"]')
            self.esperar(1)
            self.clicar_v2(By.XPATH, '//*[@id="confirm"]')
            self.esperar(.5)

            self.iframes()
            #Clicando em baixar
            print('clicando em baixar')
            self.clicar_v2(By.XPATH, '//*[@id="buttonsBar_solicitacoes"]/td[3]')
            self.esperar(1.5)

            self.escrever(By.XPATH, '//*[@id="informaçõesDaBaixa"]/tbody/tr[1]/td[1]/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td[1]/input', 'h')
            self.esperar(1.5)

            print("Confirmando baixa")
            self.clicar_v2(By.XPATH, '/html/body/div[4]/div/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td')
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(
                    transferencia_id=id,
                    status=erro,
                    dep_destino=dep_destino,
                    rec=rec,
                    qtd=qtd,
                    observacao=observacao_text
                )
                continue
            print("Aguardando alerta")
            alerta = self.obter_mensagem_alert()
            if alerta:
                print(f"[ERRO] Pulando item devido ao erro: {alerta}")
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(
                    transferencia_id=id,
                    status=alerta,
                    dep_destino=dep_destino,
                    rec=rec,
                    qtd=qtd,
                    observacao=observacao_text
                )
                continue

            print("Clicar em gravar")
            self.clicar_v2(By.XPATH, '/html/body/div[4]/div/div[1]/table/tbody/tr/td[2]/table/tbody/tr/td[2]')
            erro = self.obter_mensagem_erro()
            if erro:
                print(f"[ERRO] Pulando item devido ao erro: {erro}")
                self.fechar_aba_ate_fechar()
                enviar_status_via_api(
                    transferencia_id=id,
                    status=erro,
                    dep_destino=dep_destino,
                    rec=rec,
                    qtd=qtd,
                    observacao=observacao_text
                )
                continue
            print("Aguardando alerta")
            alerta = self.obter_mensagem_alert()
            if alerta:
                print(f"[ALERTA] Apenas um alerta: {alerta}")

            # Se chegou até aqui então funcionou!!!
            enviar_status_via_api(
                transferencia_id=id,
                status='OK',
                dep_destino=dep_destino,
                rec=rec,
                qtd=qtd,
                observacao=observacao_text,
                chave=chave
            )

            