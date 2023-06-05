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

class CamaraCrawler:

    def __init__(self, termos, projeto):
        # self.termos_lista = termos
        # self.termos = [ " "+t+" " for t in termos.keys() ]

        self.termos_lista = {termo.lower(): valor for termo, valor in termos.items()}
        self.termos = [ t.lower() for t in termos.keys() ]
        self.projeto = projeto
        self.orgao_id = 2
        self.all_tramites_hash = self.get_all_tramites()
    
    def __str__(self) -> str:
        return f'CamaraCrawler({self.termos_lista}, {self.projeto})'
    
    def get_all_tramites(self):
        Session = sessionmaker(bind=db.run())
        session = Session()
        data = datetime.now() - timedelta(days=15)
        tramites = session.query(Tramites).filter(Tramites.orgaos_id == self.orgao_id, Tramites.created_at >= data).all()
        if not tramites:
            return []
        return tramites
    
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

    def _select_termos(self, dados):
        print("\n------------ Selecionando termos")
        mask = dados['texto'].str.contains('|'.join(self.termos))
        seleciona = dados[mask].copy()
        seleciona['termo'] = seleciona['texto'].str.extract(f"({'|'.join(self.termos)})")
        seleciona['termo'] = seleciona['termo'].str.strip()
        seleciona['termos_id'] = seleciona['termo'].map(self.termos_lista)
        print('Tramitaçãoes com Termos encontrados: ', len(seleciona))
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

        # print('Tramitações com Termos_ID: ', seleciona['termos_id'])
        # print('Tramitações com Termos: ', seleciona['termo'])
        # input('------\n')

        print('Tramitações com Termos encontrados:', len(seleciona))
        return seleciona
    
    def make_hash(self, texto):
        return hashlib.md5(texto.encode()).hexdigest()
    
    def verifica_tramite(self, hash):
        all_hash = [tramite.hashing for tramite in self.all_tramites_hash]
        if hash in all_hash:
            return self.all_tramites_hash[all_hash.index(hash)]
        else:
            return None
    
    def insert_data_db(self, dados):
        print("\n------------ Inserindo dados")
        Session = sessionmaker(bind=db.run())
        session = Session()
        tramites_list = []
        for index, row in dados.iterrows():
            orgaos_id = self.orgao_id
            resumo = row['texto']
            data_origem = row['statusProposicao_dataHora']
            # print(data_origem)

            autores = row['autores']
            link_pdf = row['urlInteiroTeor']
            link_web = 'https://www.camara.leg.br/propostas-legislativas/'+str(row['id'])
            termo_id = row['termos_id']

            row = row.drop(['texto', 'termo', 'termos_id', 'autores', 'id', 'statusProposicao_dataHora'])

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
            dados.to_csv(f'modulos/camara_api/dados/dados_{str(self.projeto.id)}.csv', index=False)
            
            tramites_list = self.insert_data_db(dados)

            return set(tramites_list)
        except Exception as e:
            print(f'Erro ao executar a API-SENADO: {e}')
            return set()


        
        
