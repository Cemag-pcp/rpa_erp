from selenium.webdriver.common.by import By

from core.erp_core import BaseERP

class TransferirItem(BaseERP):

    def executar(self, rows):
        
        """
        Função principal do fluxo.
        """