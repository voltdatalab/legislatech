from datetime import datetime, timedelta
import sys
import os
from concurrent.futures import ThreadPoolExecutor
sys.path.append('./')
from modulos.notificacao_api.email.html import HTML

from sqlalchemy.sql import func
from db.models import Projetos, ProjetosHasTermos, ProjetosHasTramites, Tramites, Orgaos
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import db.conn as db
template = """
<html xmlns:v="urn:schemas-microsoft-com:vml">
<head>
    <title>{{TIT}}</title>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
     </head>
<style>
  body {
	 margin: 0;
}
 td, p {
	 font-size: 13px;
	 color: #878787;
}
 ul {
	 margin: 0 0 10px 25px;
	 padding: 0;
}
 li {
	 margin: 0 0 3px 0;
}
 h1, h2 {
	 color: black;
}
 h1 {
	 font-size: 25px;
}
 h2 {
	 font-size: 18px;
}
 a {
   color: black;
	 font-weight: bold;
	 text-decoration: none;
}
 .entire-page {
	 background: #f4f4f4;
	 width: 100%;
	 padding: 20px 0;
	 font-family: Barlow, Tahoma, Helvetica, Verdana, sans-serif;
	 line-height: 1.5;
}
 .email-body {
	 max-width: 600px;
	 min-width: 320px;
	 margin: 0 auto;
	 background: white;
	 border-collapse: collapse;
}
 .news-section {
	 padding: 20px 30px;
}
 
</style>
<table class="entire-page" style="max-width: 600px; min-width: 320px; margin: 0 auto; background: white; border-collapse: collapse;">

  <tr>

    <td>

      <table class="email-body">

        <tr>
          <td class="email-header">
            <a href="">
              <img src="{{BANNER}}" alt="banner" width="100%">
            </a>
          </td>
        </tr>

        <tr>

          <td class="news-section">

            <h1>{{TIT}}</h1>

            <p>
              {{INTRO}}
              <br><br>
              {{frase_tema}}
              palavras-chave:
              <code>{{temas}}.</code>
            </p>

          </td>

        </tr>

        <tr>
          <td class="news-section">
                      
            <p>{{tramites}}</p>
          </td>

        </tr>

        <tr>

        </tr>
        <tr>

        <tr>
          <td style="background: #eee;
	 padding: 20px;font-size: 14px; text-align: center;margin-bottom:15px">
            {{FOOTER}}
          </td>
        </tr>
        <tr>
          <td style="padding: 20px;font-size: 12px; text-align: center;margin-bottom:15px;font-family:monospace">
            {{FOOTER_SUB}}
          </td>
        </tr>
        <tr>
          <td style="margin-top:15px;padding:20x;text-align:center">
              <img src="{{LOGO}}" width="50px" alt="logo">
        </td>
        </tr>
        <tr>
          <td style="padding: 20px;font-size: 10px; text-align: center;margin-bottom:15px;font-family:monospace">
            <a  href="{{LINK_PRIVACY}}">Política de Privacidade</a> | <unsubscribe>Cancelar recebimento</unsubscribe>
          </td>

        </tr>
      </table>

    </td>

  </tr>

</table>


"""

class _email:
    def __init__(self, html_template, notification_title, logo, banner, notification_intro, footer, footer_sub, link_privacy, email):
        self.html_template = html_template
        self.notification_title = notification_title
        self.logo = logo
        self.banner = banner
        self.notification_intro = notification_intro
        self.footer = footer
        self.footer_sub = footer_sub
        self.link_privacy = link_privacy
        self.email = email

def get_all_projects():
    Session = sessionmaker(bind=db.run())
    with Session() as session:
        projects = (
            session.query(Projetos)
            .join(ProjetosHasTermos)
            .group_by(Projetos.id)
            .having(func.count(ProjetosHasTermos.termos_id) > 0)
            .all()
        )
        if not projects:
            raise NoResultFound("Nenhum projeto com termos encontrados.\n")
    return projects

def get_all_orgao_by_project(project_id):
    Session = sessionmaker(bind=db.run())
    with Session() as session:
        orgaos = (
            session.query(Orgaos)
            .join(Tramites)
            .join(ProjetosHasTramites)
            .filter(ProjetosHasTramites.projetos_id == project_id)
            .group_by(Orgaos.id)
            .all()
        )
        if not orgaos:
            raise NoResultFound("Nenhum orgao encontrado.\n")
    return orgaos

def verify_empty_tramites(tramites):
    count_empty = 0
    for key, value in tramites.items():
        if not value:
            count_empty += 1
    if count_empty == len(tramites):
        return True
    return False

def get_random_tramites(project_id, limite=15, past_days=7):
    Session = sessionmaker(bind=db.run())
    orgaos = get_all_orgao_by_project(project_id)
    tramites = {}
    
    with Session() as session:
        for orgao in orgaos:
            query = session.query(Tramites)\
                .join(ProjetosHasTramites)\
                .filter(ProjetosHasTramites.projetos_id == project_id)\
                .filter(Tramites.orgaos_id == orgao.id)\
                .filter(Tramites.created_at >= datetime.now() - timedelta(days=past_days))\
                .order_by(func.random())\
                .limit(limite)
            
            tmp_tramites = query.all()
            if not tmp_tramites:
                raise NoResultFound("Nenhum tramite encontrado.\n")
            
            tramites[orgao.nome] = {t.id for t in tmp_tramites}
    return tramites



def processar_projeto(projeto):
    try:
        tramites = get_random_tramites(projeto.id, limite=15, past_days=7)

        if verify_empty_tramites(tramites):
          print(" - Nenhum tramite novo encontrado para notificar")
          return

        email_obj = _email(
            html_template=template,
            notification_title="Seu relatório legislativo sobre Redes Sociais",
            logo="https://nucleo.jor.br/content/images/2022/06/landing-nucleo_logo-header.png",
            banner="https://pbs.twimg.com/profile_banners/1617523271129534467/1674594469/1500x500",
            notification_intro="Esse email foi produzido automaticamente.<p> </p> Este e-mail possui uma amostra dos Trâmites. <b>Acesse o Relatório completo em <a href='nucleo.jor.br/legislatech/'> LegislaTech</a></b>.",
            footer="""Este projeto foi desenvolvido  por <a href="https://nucleo.jor.br">Núcleo Jornalismo</a>, enviado apenas para assinantes e apoiadores. <br><br> Se recebeu isso de alguém e tem interesse, <a href="https://nucleo.jor.br/apoie/">acesse aqui para apoiar</a>.""",
            footer_sub="2023 - Brasil",
            link_privacy="https://nucleo.jor.br/privacidade/",
            email=projeto.email
        )

        print(projeto.id, projeto.nome)
        HTML(projeto.id, tramites, projeto, email_method='ses', email_ses=email_obj).execute()
    except Exception as e:
        print(e)


def main():
    projetos = get_all_projects()

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(processar_projeto, projetos)

if __name__ == '__main__':
    main()