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
from modulos.utils import summarize

from db.models import Tramites, TramiteDetalhes, TramitesHasTermos, ProjetosHasTramites

class SenadoCrawler:

    def __init__(self, termos, projeto):
        # self.termos_lista = termos
        # self.termos = [ " "+t+" " for t in termos.keys() ]


        self.termos_lista = {termo.lower(): valor for termo, valor in termos.items()}
        self.termos = [ t.lower() for t in termos.keys() ]
        self.projeto = projeto
        self.orgao_id = 3
        self.all_tramites_hash = self.get_all_tramites()

    def __str__(self) -> str:
        return f'SenadoCrawler({self.termos}, {self.projeto}, {self.orgao_id})'

    def get_all_tramites(self):
        Session = sessionmaker(bind=db.run())
        session = Session()
        data = datetime.now() - timedelta(days=15)
        tramites = session.query(Tramites).filter(Tramites.orgaos_id == self.orgao_id, Tramites.created_at >= data).all()
        if not tramites:
            return []
        return tramites

    def get_by_key(self, key, value):
        try:
            if '.' in key:
                old_key, new_key = key.split('.', 1)
                new_value = value[old_key]
                return self.get_by_key(new_key, new_value)
            else:
                return value[key]
        except (KeyError, TypeError):
            return None

    def get_last_situacao(self, df):
        print('Buscando última situação das matérias...')
        headers = {"Accept" : "application/json"}
        for index, row in df.iterrows():    
            CodigoMateria = row['CodigoMateria']

            url = 'https://legis.senado.leg.br/dadosabertos/materia/situacaoatual/'+ str(CodigoMateria)
            r = requests.get(url, headers=headers)
            situacao_atual = r.json()
            try:
                data_ultima_situ = self.get_by_key('SituacaoAtualMateria.Materias.Materia', situacao_atual)[-1]['SituacaoAtual']['Autuacoes']['Autuacao'][-1]['Situacoes']['Situacao'][-1]['DataSituacao']

                descricao_ultima = self.get_by_key('SituacaoAtualMateria.Materias.Materia', situacao_atual)[-1]['SituacaoAtual']['Autuacoes']['Autuacao'][-1]['Situacoes']['Situacao'][-1]['DescricaoSituacao']
            except:
                print('ERRO SITUACAO-----------', CodigoMateria, '------------')
                data_ultima_situ = None
                descricao_ultima = None

            df.loc[index, 'DataUltimaSituacao'] = data_ultima_situ
            df.loc[index, 'DescricaoUltimaSituacao'] = descricao_ultima
            # print("Data da última situação: ", data_ultima_situ)
            # print("Descrição da última situação: ", descricao_ultima)   
            # print("--------------------------------------------------")
        return df

    def get_urls(self, df):
        print('Buscando urls...')
        headers = {"Accept" : "application/json"}
        for index, row in df.iterrows():
            CodigoMateria = row['CodigoMateria']  
            url = 'https://legis.senado.leg.br/dadosabertos/materia/textos/' + str(CodigoMateria)
            r = requests.get(url, headers=headers)
            textos_url = r.json()
            try:
                url_pdf = self.get_by_key('TextoMateria.Materia.Textos.Texto', textos_url)[0]['UrlTexto']
                url_pagina = 'https://www.congressonacional.leg.br/materias/pesquisa/-/materia/' + str(CodigoMateria)
            except:
                print('ERRO URL-----------', CodigoMateria, '------------')
                url_pdf = None
                url_pagina = None
            
            df.loc[index, 'UrlPagina'] = url_pagina
            df.loc[index, 'UrlPdf'] = url_pdf
            # print("Url da página: ", url_pagina)
            # print("Url do pdf: ", url_pdf)
            # print("--------------------------------------------------")
        return df

    def get_tramites(self):
        print("Buscando tramitações...")
        yesterday = datetime.now() - timedelta(days=1)
        from_date = yesterday.strftime('%Y%m%d')
        
        url = f"https://legis.senado.leg.br/dadosabertos/materia/tramitando?data={from_date}"
        headers = {"Accept" : "application/json"}
        
        tramitando = []
        
        try:
            response = requests.get(url, headers=headers)
            tramites = response.json()
            print("Tramitações encontradas: ", len(tramites["ListaMateriasTramitando"]["Materias"]["Materia"]))
        except Exception as e:
            print("Erro ao buscar tramitações: ", e)
            return pd.DataFrame(columns=["erro_tramites"])

        try:
            materias = tramites["ListaMateriasTramitando"]["Materias"]["Materia"]
        except Exception as e:
            print("Erro ao buscar Materias: ", e)
            return pd.DataFrame(columns=["Erro_Materia"])
        
        for item in materias:
            dicionario = {
                            "autores": self.get_by_key('Autor', item),
                            "CodigoMateria": self.get_by_key('IdentificacaoMateria.CodigoMateria', item),
                            "SiglaCasaIdentificacaoMateria": self.get_by_key('IdentificacaoMateria.SiglaCasaIdentificacaoMateria', item),
                            "NomeCasaIdentificacaoMateria": self.get_by_key('IdentificacaoMateria.NomeCasaIdentificacaoMateria', item),
                            "SiglaSubtipoMateria": self.get_by_key('IdentificacaoMateria.SiglaSubtipoMateria', item),
                            "NumeroMateria": self.get_by_key('IdentificacaoMateria.NumeroMateria', item),
                            "AnoMateria": self.get_by_key('IdentificacaoMateria.AnoMateria', item),
                            "DescricaoIdentificacaoMateria": self.get_by_key('IdentificacaoMateria.DescricaoIdentificacaoMateria', item),
                            "IndicadorTramitando": self.get_by_key('IdentificacaoMateria.IndicadorTramitando', item),
                            "DataApresentacao": self.get_by_key('DataApresentacao', item),
                            "DataUltimaAtualizacao": datetime.strptime(self.get_by_key('DataUltimaAtualizacao', item),  '%Y-%m-%d %H:%M:%S'),
                            "texto": self.get_by_key('Ementa', item),
                            }

            tramitando.append(dicionario)

        df_tramitando = pd.DataFrame(tramitando)
        return df_tramitando

    def make_hash(self, texto):
        return hashlib.md5(texto.encode()).hexdigest()
    
    def _select_termos(self, dados):
        print("\n------------ Selecionando termos")
        mask = dados['texto'].str.contains('|'.join(self.termos))
        seleciona = dados[mask].copy()
        seleciona['termo'] = seleciona['texto'].str.extract(f"({'|'.join(self.termos)})")
        seleciona['termo'] = seleciona['termo'].str.strip()
        seleciona['termos_id'] = seleciona['termo'].map(self.termos_lista)

        print("Tramites com os termos encontrados: ", len(seleciona))
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
            data_origem = row['DataUltimaAtualizacao']
            autores = row['autores']
            link_pdf = row['UrlPdf']
            link_web = row['UrlPagina']
            termo_id = row['termos_id']

            row = row.drop(['texto', 'DataUltimaAtualizacao', 'autores', 'UrlPdf', 'UrlPagina', 'termos_id', 'termo'])

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
        try:
            print('---- Executando: SENADO API')
            tramites = self.get_tramites()
            # tramites.to_csv("modulos/senado_api/dados/tramitando"+str(self.projeto.id)+".csv", index=False)
            dados = self.select_termos(tramites)
            if dados.empty:
                print('Nenhum tramite encontrado com os termos selecionados')
                return set()
            df_tramitando = self.get_last_situacao(dados)
            dados = self.get_urls(df_tramitando)
            # dados.to_csv("modulos/senado_api/dados/tramitando_filtrados"+str(self.projeto.id)+".csv", index=False)
            tramites_list = self.insert_data_db(dados)

            return set(tramites_list)
        except Exception as e:
            print(f'Erro ao executar a API-SENADO: {e}')
            return set()

