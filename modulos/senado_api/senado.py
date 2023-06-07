import sys
sys.path.append('./')
from datetime import date, timedelta
from datetime import datetime
import requests
import pandas as pd

from modulos.orgao_base import BaseOrgao

class SenadoCrawler(BaseOrgao):
    def __init__(self, termos, projeto):
        super().__init__(termos=termos, projeto=projeto, orgao_id=3)

    def __str__(self) -> str:
        return f'SenadoCrawler({self.termos}, {self.projeto}, {self.orgao_id})'

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

    def modify_column_names(self, dados):
        dados = dados.rename(columns={'DataUltimaAtualizacao': 'data'}) 
        dados = dados.rename(columns={'UrlPagina': 'link'}) 
        return dados

    def execute(self):
        try:
            print('+---------------------- Executando: SENADO API')
            tramites = self.get_tramites()
            # tramites.to_csv("modulos/senado_api/dados/tramitando"+str(self.projeto.id)+".csv", index=False)
            dados = self.select_termos(tramites)

            if dados.empty:
                print('Nenhum tramite encontrado com os termos selecionados.\n')
                return set()
            df_tramitando = self.get_last_situacao(dados)
            dados = self.get_urls(df_tramitando)
            # dados.to_csv("modulos/senado_api/dados/tramitando_filtrados"+str(self.projeto.id)+".csv", index=False)
            
            dados = self.modify_column_names(dados)
            
            tramites_list = self.insert_data_db(dados)
            print('Finalizado: SENADO API: ', len(tramites_list), 'tramites encontrados.\n')

            return set(tramites_list)
        except Exception as e:
            print(f'Erro ao executar a API-SENADO: {e}')
            return set()

