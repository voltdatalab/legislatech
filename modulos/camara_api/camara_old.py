import sys
sys.path.append('./')
from datetime import date, timedelta
from datetime import datetime
import requests
import pandas as pd
import hashlib
import json
import re

from sqlalchemy.orm import sessionmaker
import db.conn as db

from db.models import Tramites, TramiteDetalhes, TramitesHasTermos, ProjetosHasTramites

class CamaraCrawler:

    def __init__(self, termos, projeto):
        self.termos_lista = termos
        self.termos = [ " "+t+" " for t in termos.keys() ]
        self.projeto = projeto
        self.orgao_id = 2
    
    def __str__(self) -> str:
        return f'CamaraCrawler({self.termos_lista}, {self.projeto})'
    
    def create_paramerters(self, termo):
        url_base = ""

        url_base = f"&keywords={termo}"
        return url_base

    def get_autores(self, df):
        lista_autores = []

        for _, row in df.iterrows():
            proposta_id = row['id']
            endpoint = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{proposta_id}/autores"
            print(endpoint)

            try:
                response = requests.get(endpoint)
                print(response.status_code)
                data = response.json()
                autores = [autor['nome'] for autor in data['dados']]
                print('Autores Tam:', len(autores))
                lista_autores.extend(autores)
            except requests.exceptions.RequestException as e:
                print("Requests exception: {}".format(e))

        df_autores = pd.DataFrame(lista_autores, columns=['autores'])
        df_autores['id'] = df['id'].tolist()

        df_final = pd.merge(df.drop_duplicates('id'), df_autores, left_on='id', right_on='id')
        return df_final

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
                                                    "statusProposicao_dataHora": str(vez['statusProposicao']['dataHora']).strip(),
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
                print("Requests exception: {}".format(e))
        df_situacao = pd.DataFrame(projetos)
        df_final = pd.merge(df, df_situacao, left_on='id', right_on='id')
        return df_final

    def get_tramites(self, termo):
        data_atual = datetime.now()
        dia_anterior = (data_atual - timedelta(1)).strftime('%d')
        mes_anterior = (data_atual - timedelta(1)).strftime('%m')
        ano_anterior = (data_atual - timedelta(1)).strftime('%Y')

        dia_hoje = (data_atual + timedelta(1)).strftime('%d')
        mes_hoje = (data_atual + timedelta(1)).strftime('%m')
        ano_hoje = (data_atual + timedelta(1)).strftime('%Y')
        termos_created = self.create_paramerters(termo)
        url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes?dataInicio={ano_anterior}-{mes_anterior}-{dia_anterior}&dataFim={ano_hoje}-{mes_hoje}-{dia_hoje}&ordem=ASC&ordenarPor=id{termos_created}"
        print(url)

        parametros = {'formato': 'json', 'itens': 100}
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
        for pagina in range(1, ultima):
            parametros = {'formato': 'json', 'itens': 100, 'pagina': pagina}
            print(url, 'PÁGINA', pagina)

            resposta = requests.get(url, parametros)
            print('Status Code:', resposta.status_code)

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
    
        
        return df_proposicoes_api

        # df_proposicoes_api.to_csv('modulos/camara_api/dados/dados.csv', index=False)

    def get_resume(self, df):
        # Deixa apenas 1 autora por proposição
        df_2 = df.drop_duplicates(subset=['id'], keep='last')
        for id, qtd in df['id'].value_counts().items():
            if qtd > 1:
                mask = df[df['id'] == id ]
                nomes = []
                for nome in mask['autores']:
                    nomes.append(nome)
                nomes = ", ".join(nomes)
                df_2.loc[df_2['id'] == id, 'autores'] = nomes

        return df_2
    
    def execute(self):
        print('---- Executando: SENADO API')
        df_final = pd.DataFrame()
        for termo, id in self.termos_lista.items():
            print(termo, id)
            tramites = self.get_tramites(termo)
            if tramites.empty:
                continue
            tramites.to_csv('modulos/camara_api/dados/tramites.csv', index=False)
            autores = self.get_autores(tramites)
            # autores.to_csv('modulos/camara_api/dados/autores.csv', index=False)
            detalhes = self.get_detalhes(autores)
            # detalhes.to_csv('modulos/camara_api/dados/detalhes.csv', index=False)
            dados = self.get_resume(detalhes)

            dados['termos_id'] = id
            

            df_final = pd.concat([df_final, dados], ignore_index=True)
        
        df_final.to_csv('modulos/camara_api/dados/dados.csv', index=False)

        
        
