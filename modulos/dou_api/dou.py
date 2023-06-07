import sys
sys.path.append('./')

from modulos.dou_api.inlabs import InlabsCrawler
from datetime import date, timedelta, datetime
import glob
from zipfile import ZipFile, BadZipFile
import os
from bs4 import BeautifulSoup
import pandas as pd
import re
import shutil

from modulos.orgao_base import BaseOrgao

class DouCrawler(BaseOrgao):

    def __init__(self, termos, projeto):
        super().__init__(termos=termos, projeto=projeto, orgao_id=1)
        
    def __str__(self) -> str:
        return f'DouCrawler({self.termos}, {self.projeto}, {self.orgao_id})'

    def get_dou_xml(self, from_date: date, to_date: date):
        inlabCrawler = InlabsCrawler(self.projeto)
        day = to_date
        
        while day >= from_date:
            inlabCrawler.download(day)
            day_str = day.strftime('%Y-%m-%d')
            for filename in glob.glob(f'modulos/dou_api/arquivos_zip/{str(self.projeto.id) + "_" +day_str}-*.zip', recursive=False):
                print(f'Extraindo {filename}')
                try:
                    with ZipFile(filename, 'r') as zip_ref:
                        zip_ref.extractall('modulos/dou_api/dados/'+str(self.projeto.id)+ "_" +day_str)
                except BadZipFile:
                    print(f'Arquivo .zip com erro: {filename}')
                finally:
                    os.remove(filename)
            day -= timedelta(days=1)
    
    def get_info_from_xml(self):
        diarios = []
        files = glob.glob('modulos/dou_api/dados/'+str(self.projeto.id)+'_*/*.xml')
        print(f'Buscando arquivos XML do projeto {self.projeto.nome}')
        print(f'Foram encontrados {len(files)} arquivos XML.')
        for filename in files:
            with open(filename, 'r') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
                article = soup.find('article')
                internal_soup = BeautifulSoup(soup.find('texto').text, 'html.parser')
                autores = internal_soup.find_all('assina')

                autores_element = soup.find('texto').find('p', class_='assina')
                autores = autores_element.text.title() if autores_element else None
       
                
                texto = internal_soup.find_all(text=True, recursive=True)
                texto = "\n".join(texto)

                padrao = r"<!\[CDATA\[(.*?)\]\]>"
                identifica = soup.find('identifica').text.strip()
                identifica = re.findall(padrao, identifica)
                identifica = identifica[0] if len(identifica) > 0 else ''

                dicionario = {
                        'id': article['id'],
                        'autores': autores,
                        'nome': article['name'],
                        'id_oficio': article.get('idoficio'),
                        'nome_pub': article['pubname'],
                        'tipo_art': article.get('arttype'),
                        'data': datetime.strptime(article['pubdate'], '%d/%m/%Y'),
                        'categoria_art': article.get('artcategory'),
                        'num_pagina': article.get('numberpage'),
                        'link': article['pdfpage'],
                        'id_materia': article.get('idmateria'),
                        'texto': texto.lower(),
                        'identifica': identifica,

                        'classe_art': article.get('artclass'),
                        'prioridade_destaque': article.get('highlightpriority'),
                        'destaque': article.get('highlight'),
                        'img_destaque': article.get('highlightimage'),
                        'nome_img_destaque': article.get('highlightimagename'),
                        'tam_art': article.get('artsize'),
                        'notas_art': article.get('artnotes'),
                        'num_edicao': article.get('editionnumber'),
                        'tipo_destaque': article.get('highlighttype')
                }
                diarios.append(dicionario)
        return diarios

    def delete_all_files(self):
        print("\n------------ Deletando arquivos")
        try:
            for folder in glob.glob('modulos/dou_api/dados/'+str(self.projeto.id)+'_*'):
                shutil.rmtree(folder)
                print("Arquivos deletados")
        except: 
            print("Não foi possivel deletar os arquivos")
    
    def modify_column_names(self, dados):
        dados['UrlPdf'] = ''
        return dados

    def execute(self):
        print('+---------------------- Executando: DIARIO OFICIAL DA UNIÃO API')
        try:
            self.get_dou_xml(date.today(), date.today())
            info_xml = self.get_info_from_xml()
            dados = pd.DataFrame(info_xml)
            dados = self.select_termos(dados)
            
            if dados.empty:
                print('Nenhum tramite encontrado com os termos selecionados.\n')
                return set()
            # dados.to_csv('modulos/dou_api/dados/'+str(self.projeto.id)+'_dados.csv', index=False)

            dados = self.modify_column_names(dados)
            tramites_list = self.insert_data_db(dados)
            self.delete_all_files()
            print('Finalizado: DOU API: ', len(tramites_list), 'tramites encontrados.\n')
            
            return set(tramites_list)
        except Exception as e:
            print(f'Erro ao executar a API-DOU: {e}')
            return set()
