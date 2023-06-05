#nohup python projeto_runner.py "esg_bot" >> logs/esg_bot.log &
# tail -f logs/esg_bot.log
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError
from db.models import Projetos, Termos, ProjetosHasTermos, ProjetosHasOrgaos, Orgaos
import db.conn as db
import sys
import datetime 
from modulos.dou_api.dou import DouCrawler
from modulos.senado_api.senado import SenadoCrawler
from modulos.camara_api.camara import CamaraCrawler
from modulos.notificacao_api.notificacao import SendNotification

class ProjectRunner:
    def __init__(self):
        Session = sessionmaker(bind=db.run())
        self.session = Session()

    def get_project_by_name(self, name):
        project = self.session.query(Projetos).filter(Projetos.nome == name).first()
        if not project:
            raise NoResultFound(f"Projeto {name} não encontrado.\n")
        return project

    def get_terms_by_project(self, project):
        terms = self.session.query(Termos).join(ProjetosHasTermos).filter(ProjetosHasTermos.projetos_id == project.id).all()
        if not terms:
            raise NoResultFound(f"Termos do projeto {project.nome} não encontrados.\n")
        return terms
    
    def get_orgao_by_project(self, project):
    
        orgaos = self.session.query(Orgaos).join(ProjetosHasOrgaos).filter(ProjetosHasOrgaos.projetos_id == project.id).all()
        if not orgaos:
            raise NoResultFound(f"Orgao do projeto {project.nome} não encontrado.\n")
        orgao_names = [orgao.nome for orgao in orgaos]
        return orgao_names

    def run(self, name):
        data = datetime.datetime.now()
        print("\n--------")
        print("--------")
        print(f"Projeto {name} iniciado")
        print(f"Data:COMEÇO {data.day}/{data.month}/{data.year} - {data.hour}:{data.minute}:{data.second}")
        print("--------")
        try:
            project = self.get_project_by_name(name)
            print(f"Projeto {name} tem id {project.id}")

            terms = self.get_terms_by_project(project)
            terms_dict = {term.nome: term.id for term in terms}
            orgao_allow = self.get_orgao_by_project(project)

            print("Termos: ", terms_dict)
            print("Orgao: ", orgao_allow)

            tramites_dou = DouCrawler(terms_dict, project).execute() if 'dou' in orgao_allow else []
            tramites_senado = SenadoCrawler(terms_dict, project).execute() if 'senado' in orgao_allow else []
            tramites_camara = CamaraCrawler(terms_dict, project).execute() if 'camara' in orgao_allow else []
    
            tramites_dou = tramites_dou[:12] if len(tramites_dou) > 12 else tramites_dou
            
            tramites = {
                'senado': tramites_senado,
                'camara': tramites_camara,
                'dou': tramites_dou
            }
          
            sendNotification = SendNotification(tramites, project)
            sendNotification.execute()



        except NoResultFound as e:
            print(" - NoResultFound")
            print(e)
        except Exception as e:
            print(" - Erro Geral")
            print(e)
        finally:
            data = datetime.datetime.now()
            print("--------")
            print(f"Projeto {name} finalizado")
            print(f"Data:FIM    {data.day}/{data.month}/{data.year} - {data.hour}:{data.minute}:{data.second}")
            print("--------\n\n\n\n")

        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        try:
            runner = ProjectRunner()
            runner.run(sys.argv[1])
        except OperationalError as e:
            print("Erro ao conectar com o banco de dados")
            print(e)    
        
    else:
        print("Não foi passado o nome do projeto")
        print("Exemplo: python projeto_runner.py \"esg_bot\"")


