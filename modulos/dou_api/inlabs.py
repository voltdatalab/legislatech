from datetime import date
import requests
import os
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings()

from datetime import date, timedelta

load_dotenv()

class InlabsCrawler:
    def __init__(self, projeto):
        self.projeto = projeto
        self.login = os.getenv("INLABS_LOGIN")
        self.senha = os.getenv("INLABS_PASSWORD")
        self.tipo_dou = "DO1 DO2 DO3 DO1E DO2E DO3E"
        self.url_login = "https://inlabs.in.gov.br/logar.php"
        self.url_download = "https://inlabs.in.gov.br/index.php?p="
        self.payload = {"email": self.login, "password": self.senha}
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        self.session = requests.Session()
        self.session.verify = False
    
    def download(self, day=date.today()):
        try:
            response = self.session.request("POST", self.url_login, data=self.payload, headers=self.headers)
            if self.session.cookies.get('inlabs_session_cookie'):
                cookie = self.session.cookies.get('inlabs_session_cookie')
            else:
                print("Falha ao obter cookie. Verifique suas credenciais")
                return
            
            ano = day.strftime("%Y")
            mes = day.strftime("%m")
            dia = day.strftime("%d")
            data_completa = ano + "-" + mes + "-" + dia
            
            for dou_secao in self.tipo_dou.split(' '):
                print("Aguarde Download...")
                url_arquivo = self.url_download + data_completa + "&dl=" + data_completa + "-" + dou_secao + ".zip"
                cabecalho_arquivo = {'Cookie': 'inlabs_session_cookie=' + cookie, 'origem': '736372697074'}
                response_arquivo = self.session.request("GET", url_arquivo, headers=cabecalho_arquivo)
                if response_arquivo.status_code == 200:
                    print('Arquivo Encontrado. Salvando...')
                    nome_arquivo = str(self.projeto.id)+ "_" +data_completa + "-" + dou_secao + ".zip"
                    caminho_arquivo = os.path.join("modulos/dou_api/arquivos_zip", nome_arquivo)
                    caminho_absoluto = os.path.abspath(caminho_arquivo)
                    with open(caminho_absoluto, "wb") as f:
                        f.write(response_arquivo.content)
                    print("Arquivo {} salvo.".format(caminho_absoluto))
                    del response_arquivo
                elif response_arquivo.status_code == 404:
                    print("Arquivo não encontrado: {}".format(data_completa + "-" + dou_secao + ".zip"))
        
        except requests.exceptions.ConnectionError:
            self.download(day)