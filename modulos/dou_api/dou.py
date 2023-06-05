import sys
sys.path.append('./')

from modulos.dou_api.inlabs import InlabsCrawler
from datetime import date, timedelta
import glob
from zipfile import ZipFile, BadZipFile
import os
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import re
from sqlalchemy.orm import sessionmaker
import hashlib
import json
import shutil


from db.models import Tramites, TramiteDetalhes, TramitesHasTermos, ProjetosHasTramites
from modulos.utils import summarize

import db.conn as db

class DouCrawler:
    def __init__(self, termos, projeto):
        # self.termos_lista = termos
        # self.termos = [ " "+t+" " for t in termos.keys() ]
        self.termos_lista = {termo.lower(): valor for termo, valor in termos.items()}
        self.termos = [ t.lower() for t in termos.keys() ]
        self.projeto = projeto
        self.orgao_id = 1
        self.all_tramites_hash = self.get_all_tramites()
    
    def __str__(self) -> str:
        return f'DouCrawler({self.termos}, {self.projeto}, {self.orgao_id})'

    def get_all_tramites(self):
        Session = sessionmaker(bind=db.run())
        session = Session()
        data = datetime.now() - timedelta(days=15)
        tramites = session.query(Tramites).filter(Tramites.orgaos_id == self.orgao_id, Tramites.created_at >= data).all()
        if not tramites:
            return []
        return tramites

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

    def _select_termos(self, dados):
        print("\n------------ Selecionando termos")
        mask = dados['texto'].str.contains('|'.join(self.termos))
        seleciona = dados[mask].copy()
        seleciona['termo'] = seleciona['texto'].str.extract(f"({'|'.join(self.termos)})")
        seleciona['termo'] = seleciona['termo'].str.strip()
        seleciona['termos_id'] = seleciona['termo'].map(self.termos_lista)
        print('Tramitações com Termos encontrados: ', len(seleciona))
        return seleciona

    def has_match(self, texto, termos):
        regex = re.compile(fr'\b({"|".join(termos)})\b', flags=re.IGNORECASE)
        return bool(regex.search(texto))

    def select_termos(self, dados):
        print("\n------------ Selecionando termos")
        seleciona = dados[dados['texto'].apply(lambda x: self.has_match(x, self.termos))].copy()
        seleciona['termo'] = seleciona['texto'].str.extract(fr"({'|'.join(self.termos)})", flags=re.IGNORECASE)
        seleciona['termo'] = seleciona['termo'].str.strip()

        correspondentes = []
        for termo in seleciona['termo']:
            
            correspondente = self.termos_lista[termo]
            correspondentes.append(correspondente)

        seleciona['termos_id'] = correspondentes

        print('Tramitações com Termos_ID: ', seleciona['termos_id'])
        print('Tramitações com Termos: ', seleciona['termo'])
        # input('------\n')

        print('Tramitações com Termos encontrados:', len(seleciona))
        return seleciona


    def verifica_tramite(self, hash):
        all_hash = [tramite.hashing for tramite in self.all_tramites_hash]
        if hash in all_hash:
            return self.all_tramites_hash[all_hash.index(hash)]
        else:
            return None
        
    def make_hash(self, texto):
        return hashlib.md5(texto.encode()).hexdigest()
              
    def insert_data_db(self, dados):
        print("\n------------ Inserindo dados")
        Session = sessionmaker(bind=db.run())
        session = Session()
        tramites_list = []

        for index, row in dados.iterrows():
            orgaos_id = self.orgao_id
            resumo = row['texto']
            data_origem = row['data']
            autores = row['autores']
            link_pdf = ''
            link_web = row['link']
            termo_id = row['termos_id']

            row = row.drop('texto')
            row = row.drop('data')
            row = row.drop('autores')
            row = row.drop('link')
            row = row.drop('termos_id')
            row = row.drop('termo')
            detalhes = json.dumps(row.to_dict())
            
            hashing_payload = str(detalhes) + str(resumo) + str(data_origem) + str(autores) + str(link_pdf) + str(link_web)

            hash = self.make_hash(hashing_payload)
            tramite = self.verifica_tramite(hash)

            if not tramite:
                print('Tramite não Existe')
                resumo_ia = summarize(resumo, self.projeto.openai_token) if self.projeto.openai_token else ''
                tramite = Tramites(
                    orgaos_id=orgaos_id,
                    resumo=resumo,
                    resumo_ia=resumo_ia,
                    data_origem=data_origem,
                    autores=autores,
                    link_pdf=link_pdf,
                    link_web=link_web,
                    hashing=hash
                )

                try:
                    session.add(tramite)
                    session.commit()
              
                    print(f"Tramite inserido {tramite.id}")

                    tramite_termo = TramitesHasTermos(
                        tramites_id=tramite.id,
                        termos_id=termo_id
                    )
                    session.add(tramite_termo)
                    session.commit()
                    print("Tramite_termo inserido")

                    tramite_detalhes = TramiteDetalhes(
                        tramites_id=tramite.id,
                        json=detalhes
                
                    )
                    session.add(tramite_detalhes)
                    session.commit()
                    print("Tramite_detalhes inserido")

                    tramites_list.append(tramite.id)
                except Exception as e:
                    session.rollback()
                    print(f'Erro ao inserir tramite {tramite.id}')
                    print(e)
            else:
                print(f"Tramite já existe {tramite.id}")

            projeto_id = self.projeto.id
            tramite_projeto = session.query(ProjetosHasTramites).filter_by(tramites_id=tramite.id, projetos_id=projeto_id).first()

            if not tramite_projeto:
                print(f"* ProjetosHasTramites não existe")
                tramite_projeto = ProjetosHasTramites(
                    tramites_id=tramite.id,
                    projetos_id=projeto_id
                )
                session.add(tramite_projeto)
                session.commit()
                print(f"+ ProjetosHasTramites inserido:\n -Projeto_ID {tramite_projeto.projetos_id} \n -Tramite_ID {tramite_projeto.tramites_id}\n")
                tramites_list.append(tramite.id)
            else:
                print(f"ProjetosHasTramites já existe:\n -Projeto_ID {tramite_projeto.projetos_id} \n -Tramite_ID {tramite_projeto.tramites_id}\n")
        session.close()
        return tramites_list

    def delete_all_files(self):
        print("\n------------ Deletando arquivos")
        try:
            for folder in glob.glob('modulos/dou_api/dados/'+str(self.projeto.id)+'_*'):
                shutil.rmtree(folder)
                print("Arquivos deletados")
        except: 
            print("Não foi possivel deletar os arquivos")
        
    def execute(self):
        print('---- Executando: DIARIO OFICIAL DA UNIÃO API')
        try:
            self.get_dou_xml(date.today(), date.today())
            info_xml = self.get_info_from_xml()
            dados = pd.DataFrame(info_xml)
            dados = self.select_termos(dados)
            dados.to_csv('modulos/dou_api/dados/'+str(self.projeto.id)+'_dados.csv', index=False)
            tramites_list = self.insert_data_db(dados)
            self.delete_all_files()
            return set(tramites_list)
        except Exception as e:
            print(f'Erro ao executar a API-DOU: {e}')
            return set()
