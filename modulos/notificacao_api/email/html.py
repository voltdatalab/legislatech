import json
import db.conn as db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from db.models import EmailConf, Tramites, TramitesHasTermos, Termos, TramiteDetalhes, ProjetosHasTermos
from modulos.notificacao_api.email.send_email import Email

from datetime import datetime

class HTML:
    def __init__(self, email_id, tramites, projeto):
        self.projeto = projeto
        self.tramites = tramites
        self.email_id = email_id
        self.email = self.get_email_conf()
        self.template = self.email.html_template

    def get_email_conf(self):
        Session = sessionmaker(bind=db.run())
        session = Session()
        email_conf = session.query(EmailConf).filter(EmailConf.id == self.email_id).first()
        if not email_conf:
            raise NoResultFound(f"EmailConf {self.email_id} não encontrado.\n")
        return email_conf

    def get_tramites_by_ids(self, tramites):
        Session = sessionmaker(bind=db.run())
        session = Session()
        tramites = session.query(Tramites).filter(Tramites.id.in_(tramites)).all()
        if not tramites:
            raise NoResultFound(f"Tramites {tramites} não encontrado.\n")
        return tramites

    def verify_termos(self, termos_tramites, termos_projetos):
        for termo in termos_tramites:
            if termo in termos_projetos:
                return termo
        return termos_tramites[0]

    def get_termos_by_projeto(self):
        Session = sessionmaker(bind=db.run())
        session = Session()
        termos = session.query(Termos).join(ProjetosHasTermos).filter(ProjetosHasTermos.projetos_id == self.projeto.id).all()
        if not termos:
            raise NoResultFound(f"Termos {termos} não encontrado.\n")
        termos = [termo.nome.upper() for termo in termos]
        return termos
    
    def get_termos_by_tramite(self, tramite_id):
        Session = sessionmaker(bind=db.run())
        session = Session()
        termos = session.query(Termos).join(TramitesHasTermos).filter(TramitesHasTermos.tramites_id == tramite_id).all()
        if not termos:
            raise NoResultFound(f"Termos {termos} não encontrado.\n")
        termos = [termo.nome.upper() for termo in termos]
        termo = self.verify_termos(termos, self.get_termos_by_projeto())
        return termo

    def get_tramites_detalhes(self, tramite_id):
        Session = sessionmaker(bind=db.run())
        session = Session()
        tramites_detalhes = session.query(TramiteDetalhes).filter(TramiteDetalhes.tramites_id == tramite_id).first()
        if not tramites_detalhes:
            raise NoResultFound(f"TramitesDetalhes {tramites_detalhes} não encontrado.\n")
        return tramites_detalhes
    
    def monta_valores(self, tramite, termos, orgao):
        valores = {}
        # print(tramite.data_origem)
        data = datetime.strptime(tramite.data_origem, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
        
        valores['data'] = data
        valores['tema'] = ', '.join(termos)
        valores['nome'] = tramite.autores if tramite.autores else None

        valores['resumo'] = tramite.resumo_ia if tramite.resumo_ia else tramite.resumo[:500] + '...'
        valores['url_pdf'] = tramite.link_pdf if tramite.link_pdf else None
        valores['url_pagina'] = tramite.link_web if tramite.link_web else None

        tramite_detalhes = self.get_tramites_detalhes(tramite.id)
        detalhes = tramite_detalhes.json
        detalhes = json.loads(detalhes)
        # print(f'\n------------------------ DETALHES {orgao.upper()}------------------------')
        # print(detalhes)
        if orgao == 'dou':
            pagina = detalhes['num_pagina']
            edicao = detalhes['num_edicao']
            valores['titulo'] = f"DOU: {data} / #{edicao} / pag. {pagina}"
        
        if orgao == 'camara':
            valores['titulo'] = f"CÂMARA: {detalhes['siglaTipo']} {detalhes['numero']}/{detalhes['ano']}"
            valores['tramitacao'] = detalhes['statusProposicao_descricaoTramitacao']
            valores['situacao'] = detalhes['statusProposicao_descricaoSituacao']

        if orgao == 'senado':
            valores['titulo'] = f"SENADO: {detalhes['DescricaoIdentificacaoMateria']}"
            valores['tramitacao'] = detalhes['IndicadorTramitando']
            valores['situacao'] = detalhes['DescricaoUltimaSituacao']

        if not valores['nome']:
            del valores['nome']

        if not valores['url_pdf']:
            del valores['url_pdf']
        
        if not valores['url_pagina']:
            del valores['url_pagina']

        return valores
     
    def cria_html(self, tramite, termos, orgao):

        valores = self.monta_valores(tramite, termos, orgao)

        insert_li = ""
        for k, v in valores.items():

            if k == 'resumo':
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Resumo da descrição:</strong> {v.capitalize()}
                </li>
                """

            if k == 'data':
                insert_li += f"""
                    <li style="font-size:14px;list-style-type:square;">
                        <strong>Última atualização:</strong> {v} 
                    </li>
                """
            
            if k == 'nome':
       
                if len(v) > 130:
                    v = v[:127] + '...'
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Nome:</strong> {v}
                </li>"""
                
            if k == 'tema':
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Palavra-chave:</strong> {v}
                </li>"""

            if k == 'tramitacao':
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Tramitação:</strong> {v}
                </li>
                """

            if k == 'situacao':
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Situação:</strong> {v}
                </li>
                """

            if k == 'url_pdf':
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Link para PDF:</strong> <a style="color: black; font-weight: bold;" href="{v}">{v}</a>
                </li>"""
            
            if k == 'url_pagina':
                insert_li += f"""
                <li style="font-size:14px;list-style-type:square;">
                    <strong>Link para Página:</strong> <a style=" color: black; font-weight: bold;" href="{v}">{v}</a>
                </li>"""

        tramite = f"""
            <div class="text-element paragraph">
                <div
                    style="text-align: left;">
                    <p style="text-align: left;">
                        {valores['titulo']}
                    </p>
                    <ul style="color: rgb(51, 51, 51);">

                        {insert_li}

                    </ul>
                </div>
            </div>
        """

        return tramite + """ <hr style="height:1px;background-color:#eeeeee">"""

    def insere_configuracoes(self):

        TIT = self.email.notification_title
        LOGO = self.email.logo
        BANNER = self.email.banner
        INTRO = self.email.notification_intro
        FOOTER = self.email.footer
        FOOTER_SUB = self.email.footer_sub
        LINK_PRIVACY = self.email.link_privacy

        self.template = self.template.replace("{{TIT}}", str(TIT))
        self.template = self.template.replace("{{LOGO}}", str(LOGO))
        self.template = self.template.replace("{{BANNER}}", str(BANNER))
        self.template = self.template.replace("{{INTRO}}", str(INTRO))
        self.template = self.template.replace("{{FOOTER}}", str(FOOTER))
        self.template = self.template.replace("{{FOOTER_SUB}}", str(FOOTER_SUB))
        self.template = self.template.replace("{{LINK_PRIVACY}}", str(LINK_PRIVACY))

    def monta_tramites(self):
        print("\nMontando template:")
        
        tramites_dou = self.get_tramites_by_ids(self.tramites['dou']) if self.tramites['dou'] else [] 
        tramites_senado = self.get_tramites_by_ids(self.tramites['senado']) if self.tramites['senado'] else []
        tramites_camara = self.get_tramites_by_ids(self.tramites['camara']) if self.tramites['camara'] else []
        
        all_termos = []
        tramites_html = ''

        tramites = [
            (tramites_senado, 'senado'),
            (tramites_camara, 'camara'),
            (tramites_dou, 'dou')
        ]


        for tramite_list, tipo in tramites:
            print(f"--Quantidade de Tramites {tipo.upper()}: {len(tramite_list)}")
            for tramite in tramite_list:
                print(f"----Tramite {tipo.upper()}: {tramite.id}")
                termos = self.get_termos_by_tramite(tramite.id)
                all_termos.extend(termos)
                tramites_html += self.cria_html(tramite, termos, tipo)

        all_tramites = list(set(tramites_dou + tramites_senado + tramites_camara))
        all_termos = list(set(all_termos))
        
        n_tramites = len(all_tramites)
        if n_tramites == 1:
            frase_tema = f"Foi detectado {n_tramites} trâmite parlamentar envolvendo a"
        else:
            frase_tema = f"Foram detectados {n_tramites} trâmites parlamentares envolvendo as"

        self.template = self.template.replace("{{tramites}}", str(tramites_html))
        self.template = self.template.replace("{{frase_tema}}", str(frase_tema))

        temas = all_termos
        temas = [t.replace('.', '') for t in temas]
        temas = ', '.join(temas)
        self.template = self.template.replace("{{temas}}", str(temas))

        self.insere_configuracoes()

        with open("modulos/notificacao_api/dados/email_"+ str(self.email_id) +".html", "w") as f:
            f.write(self.template)

    def execute(self):
        # print(f"Email {self.email}")
        print(f"Enviando email para {self.email_id}")
        self.monta_tramites()
        
        Email.sendy(self.template, self.email)


        
        