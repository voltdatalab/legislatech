import sys
sys.path.append('./')
from datetime import date, timedelta
from datetime import datetime
import requests
import pandas as pd
import hashlib
import json
import re
import hashlib

from sqlalchemy.orm import sessionmaker
import db.conn as db
from modulos.utils import summarize

from db.models import Tramites, TramiteDetalhes, TramitesHasTermos, ProjetosHasTramites
from modulos.orgao_base import BaseOrgao


class CamaraCrawler(BaseOrgao):

    def __init__(self, termos, projeto):
        super().__init__(termos=termos, projeto=projeto, orgao_id=2)
    
    def __str__(self) -> str:
        return f'CamaraCrawler({self.termos_lista}, {self.projeto})'
    
    def create_paramerters(self, termo):
        url_base = ""

        url_base = f"&keywords={termo}"
        return url_base

    def get_autores(self, df):

        for i, row in df.iterrows():
            proposta_id = row['id']
            endpoint = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{proposta_id}/autores"
            # print(endpoint)

            try:
                response = requests.get(endpoint)
                # print(response.status_code)
                data = response.json()
                autores = [autor['nome'] for autor in data['dados']]
                # print('Autores Tam:', len(autores))
                # print(autores)
                df.at[i, 'autores'] = ", ".join(autores)
            except requests.exceptions.RequestException as e:
                print("Requests exception: {}".format(e))
        return df

    def get_detalhes(self, df):
        # Busca a última situação das proposicoes
        endpoint = "https://dadosabertos.camara.leg.br/api/v2/proposicoes/"

        projetos = []
        parametros = {'formato': 'json'}
        for num, row in df.iterrows():
            id = row['id']
            url = endpoint + id
            try:
                r = requests.get(url, parametros)
                # print(f'Status Code: {r.status_code}')
                vez =  r.json()['dados']
                dicionario = {"id": str(vez['id']).strip(),
                                        "uri": str(vez['uri']).strip(),
                                                    "siglaTipo": str(vez['siglaTipo']).strip(),
                                                    "codTipo": str(vez['codTipo']).strip(),
                                                    "numero": str(vez['numero']).strip(),
                                                    "ano": str(vez['ano']).strip(),
                                                    "ementa": str(vez['ementa']).strip(),
                                                    "dataApresentacao": str(vez['dataApresentacao']).strip(),
                                                    "statusProposicao_dataHora": datetime.strptime(str(vez['statusProposicao']['dataHora']).strip(), '%Y-%m-%dT%H:%M'),
                                                    "statusProposicao_siglaOrgao": str(vez['statusProposicao']['siglaOrgao']).strip(),
                                                    "statusProposicao_siglaOrgao": str(vez['statusProposicao']['siglaOrgao']).strip(),
                                                    "statusProposicao_descricaoTramitacao": str(vez['statusProposicao']['descricaoTramitacao']).strip(),
                                                    "statusProposicao_descricaoSituacao": str(vez['statusProposicao']['descricaoSituacao']).strip(),
                                                    "statusProposicao_despacho": str(vez['statusProposicao']['despacho']).strip(),
                                                    "keywords": str(vez['keywords']).strip(),
                                                    "urlInteiroTeor": str(vez['urlInteiroTeor']).strip(),
                                                    "uriAutores": str(vez['uriAutores']).strip()
                                                    }

                projetos.append(dicionario)
            except requests.exceptions.RequestException as e:
                print("Requests excepti\on: {}".format(e))
        df_situacao = pd.DataFrame(projetos)
        df_columns = df.columns
        df_columns = df_columns.drop(['texto', 'termo', 'termos_id', 'autores', 'id'])
        df_situacao = df_situacao.drop(columns=df_columns)

        df_final = pd.merge(df, df_situacao, left_on='id', right_on='id')
        return df_final

    def get_tramites(self):
        data_atual = datetime.now()
        dia_anterior = (data_atual - timedelta(1)).strftime('%d')
        mes_anterior = (data_atual - timedelta(1)).strftime('%m')
        ano_anterior = (data_atual - timedelta(1)).strftime('%Y')

        dia_hoje = (data_atual + timedelta(1)).strftime('%d')
        mes_hoje = (data_atual + timedelta(1)).strftime('%m')
        ano_hoje = (data_atual + timedelta(1)).strftime('%Y')
        url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?dataInicio={ano_anterior}-{mes_anterior}-{dia_anterior}&dataFim={ano_hoje}-{mes_hoje}-{dia_hoje}&ordem=ASC&ordenarPor=id"
        # print(url)

        parametros = {'formato': 'json', 'itens': 1000}
        resposta = requests.get(url, parametros)
        print('Status Code:', resposta.status_code)
        for vez in resposta.json()['links']:
            conta = {"rel": vez['rel'].strip(), "href": vez['href'].strip()}

        # Testa se a url tem alguma proposicao
        ultimo = conta['rel']
        if ultimo != 'last':
            column_names = ["id"]
            df = pd.DataFrame(columns=column_names)
            return df

        link_ultimo = str(conta['href'].strip())
        print(f'Link da última página: {link_ultimo}')
    
        regex = r"&pagina=(\d+)&itens="
        matches = re.search(regex, link_ultimo)
        ultima = int(matches.group(1)) + 1
        print("\n-------------------------")
        proposicoes = []
        # Faz a iteração a partir do número de páginas encontrado
        print(f'Número de páginas: {ultima}')
        for pagina in range(1, ultima):
            parametros = {'formato': 'json', 'itens': 1000, 'pagina': pagina}
            # print(url, 'PÁGINA', pagina)

            resposta = requests.get(url, parametros)
            # print('Status Code:', resposta.status_code)

            # Captura os dados
            for vez in resposta.json()['dados']:
                dicionario = {"id": str(vez['id']).strip(),
                                                    "uri": str(vez['uri']).strip(),
                                                    "siglaTipo": str(vez['siglaTipo']).strip(),
                                                    "codTipo": str(vez['codTipo']).strip(),
                                                    "numero": str(vez['numero']).strip(),
                                                    "ano": str(vez['ano']).strip(),
                                                    "ementa": str(vez['ementa']).strip()
                                                    }
                proposicoes.append(dicionario)

        df_proposicoes_api = pd.DataFrame(proposicoes)
        df_proposicoes_api['texto'] = df_proposicoes_api['ementa']
        
        print('Tramitações encontradas: ', len(df_proposicoes_api))
        
        return df_proposicoes_api

        # df_proposicoes_api.to_csv('modulos/camara_api/dados/dados.csv', index=False)

    def modify_column_names(self, dados):
        dados = dados.rename(columns={'statusProposicao_dataHora': 'data'}) 
        dados = dados.rename(columns={'urlInteiroTeor': 'UrlPdf'}) 
        dados['link'] = 'https://www.camara.leg.br/propostas-legislativas/'+dados['id'].astype(str)
        dados = dados.rename(columns={'id': 'id_camara'})
        return dados

    def execute(self):
        print('---- Executando: CAMARA API')
        try:
            tramites = self.get_tramites()
            termos = self.select_termos(tramites)
            if termos.empty:
                print('Nenhum tramite encontrado com os termos selecionados')
                return set()
            # termos.to_csv('modulos/camara_api/dados/termos.csv', index=False)
            autores = self.get_autores(termos)
            # autores.to_csv('modulos/camara_api/dados/autores.csv', index=False)
            dados = self.get_detalhes(autores)
            # dados.to_csv(f'modulos/camara_api/dados/dados_{str(self.projeto.id)}.csv', index=False)
            
            dados = self.modify_column_names(dados)
            
            tramites_list = self.insert_data_db(dados)

            return set(tramites_list)
        except Exception as e:
            print(f'Erro ao executar a API-SENADO: {e}')
            return set()


        
        
