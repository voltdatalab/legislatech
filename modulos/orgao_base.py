import sys
sys.path.append('./')

from modulos.utils import summarize

import db.conn as db
from sqlalchemy.orm import sessionmaker
from datetime import timedelta, datetime
from db.models import Tramites, TramiteDetalhes, TramitesHasTermos, ProjetosHasTramites

import hashlib
import re
import json

class BaseOrgao:
    def __init__(self, termos, projeto, orgao_id):
        self.Session = sessionmaker(bind=db.run())
        self.termos_lista = {termo.lower(): valor for termo, valor in termos.items()}
        self.termos = [ t.lower() for t in termos.keys() ]
        self.projeto = projeto
        self.orgao_id = orgao_id
        self.all_tramites_hash = self.get_all_tramites()
        
    def get_all_tramites(self):
        with self.Session() as session:
            data = datetime.now() - timedelta(days=15)
            tramites = session.query(Tramites).filter(Tramites.orgaos_id == self.orgao_id, Tramites.created_at >= data).all()
            if not tramites:
                return []
        return tramites

    def verifica_tramite(self, hash):
        all_hash = [tramite.hashing for tramite in self.all_tramites_hash]
        if hash in all_hash:
            return self.all_tramites_hash[all_hash.index(hash)]
        else:
            return None
        
    def make_hash(self, texto):
        return hashlib.md5(texto.encode()).hexdigest()
    
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
            correspondente = self.termos_lista[termo.lower()]
            correspondentes.append(correspondente)

        seleciona['termos_id'] = correspondentes

        # print('Tramitações com Termos_ID: ', seleciona['termos_id'])
        # print('Tramitações com Termos: ', seleciona['termo'])

        print('Tramitações com Termos encontrados:', len(seleciona))
        return seleciona

    def get_termosid_by_tramite(self, tramite):
        with self.Session() as session:
            termos_tramite_list = []
            termos_tramite = session.query(TramitesHasTermos).filter_by(tramites_id=tramite.id).all()
            for termo_tramite in termos_tramite:
                termos_tramite_list.append(termo_tramite.termos_id)
        return termos_tramite_list
    
    def insert_data_db(self, dados):
        print("\n------------ Inserindo dados")
        with self.Session() as session:
            tramites_list = []

            for index, row in dados.iterrows():
                orgaos_id = self.orgao_id
                resumo = row['texto']
                data_origem = row['data']
                autores = row['autores']
                link_pdf = row['UrlPdf']
                link_web = row['link']
                termo_id = row['termos_id']

                row = row.drop(['texto', 'data', 'autores', 'UrlPdf', 'link', 'termos_id', 'termo'])

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

                    termos_tramite_list = self.get_termosid_by_tramite(tramite)
                    if termo_id not in termos_tramite_list:
                        print(f"Termos já existente no Tramite: {termos_tramite_list}")
                        tramite_termo = TramitesHasTermos(
                            tramites_id=tramite.id,
                            termos_id=termo_id
                        )
                        session.add(tramite_termo)
                        session.commit()
                        print(f"*Novo Tramite_termo inserido:\n -Tramite_ID {tramite_termo.tramites_id} \n -Termo_ID {tramite_termo.termos_id}\n")

                    print(f"+ ProjetosHasTramites inserido:\n -Projeto_ID {tramite_projeto.projetos_id} \n -Tramite_ID {tramite_projeto.tramites_id}\n")
                    tramites_list.append(tramite.id)
                else:
                    print(f"ProjetosHasTramites já existe:\n -Projeto_ID {tramite_projeto.projetos_id} \n -Tramite_ID {tramite_projeto.tramites_id}\n")

        return tramites_list
