import threading
from projeto_runner import ProjectRunner
import os
import sys

from sqlalchemy.sql import func
from db.models import Projetos, ProjetosHasTermos
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
import db.conn as db


logs_directory = '.logs'

def print_to_log(*args, **kwargs):
    log_filename = f'{threading.current_thread().name}.txt'
    log_path = os.path.join(logs_directory, log_filename)
    with open(log_path, 'a') as file:
        output = ' '.join(str(arg) for arg in args)
        print(output, **kwargs, file=file, end='')
    sys.stderr.write(output)

sys.stdout.write = print_to_log

def run_project_runner(nome_bot):
    try:
        runner = ProjectRunner()
        runner.run(nome_bot)
    except Exception as e:
        print(f"Ao rodar ProjectRunner com o botname {nome_bot} ")
        print(e)

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
    return [p.nome for p in projects]

if __name__ == '__main__':
    os.makedirs(logs_directory, exist_ok=True)

    nomes_bots = get_all_projects()
    print(f"Bots Rodando: {nomes_bots}")
    print(f"Bots Rodando Tamanho: len({nomes_bots})\n")
    threads = []
    for nome_bot in nomes_bots:
        thread = threading.Thread(target=run_project_runner, args=(nome_bot,), name=nome_bot)
        threads.append(thread)
        thread.start()
    
    # Aguardar todas as threads concluírem
    for thread in threads:
        thread.join()
