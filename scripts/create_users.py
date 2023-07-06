import sys
sys.path.append('./')

import requests
import jwt
from datetime import datetime as date
import os
import hashlib
from dotenv import load_dotenv
import random
import hashlib
load_dotenv()

import db.conn as db

import db.conn as db
from sqlalchemy.orm import sessionmaker
from db.models import Projetos, ProjetosHasOrgaos, Orgaos

definicoes = {
    "prod_LmXWnIYLZz5hw7" : {
        "tier_name_debug": "Tecnologia",
        "qtd_termos": 3,
        "orgao": ['camara', 'senado'],
        "qtd_email": 1,
        "periodicidade_email": ['semanal']
    },
    "prod_LmXXyoCQqlr0Fp" : {
        "tier_name_debug": "Missão",
        "qtd_termos": 10,
        "orgao": ['camara', 'senado', 'dou'],
        "qtd_email": 1,
        "periodicidade_email": ['semanal', 'diario']
    }
}

API_KEY = os.getenv("GHOST_API")

def generate_token():
    key = API_KEY

    id, secret = key.split(':')
    iat = int(date.now().timestamp())

    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': '/admin/'
    }

    token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)
    return token

def get_ghost_users():
    token = generate_token()

    url = 'https://nucleo.jor.br/ghost/api/admin/members/?filter=status:paid&limit=all'
    headers = {'Authorization': 'Ghost {}'.format(token)}
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        members = []
        for m in r.json()['members']:
            email = m['email']
            product_id = m['subscriptions'][0]['price']['tier']['id']
            name = m['name']
            if product_id in ['prod_LmXXyoCQqlr0Fp', 'prod_LmXWnIYLZz5hw7']:
                username = email.split('@')[0].replace('.', '')
                seed = str(random.randint(1, 1000000))  # Gerar uma semente aleatória
                data = email + seed  # Concatenar semente ao email
                h = hashlib.shake_256(data.encode())
                hex_digest = h.hexdigest(3)
                bot_name = f'{username}_{hex_digest}'

                cliente = name.replace(' ', '_').lower() if isinstance(name, str) else username
                members.append({
                    "cliente": cliente,
                    "email": email,
                    "product_id": product_id,
                    "bot_name": bot_name
                })

        return members
    except Exception as e:
        print(e)
        return [] 

def get_all_projetos_email():
    Session = sessionmaker(bind=db.run())
    with Session() as session:

        tramites = session.query(Projetos).all()
        if not tramites:
            return []
    tramites_email = [ t.email for t in tramites]

    return tramites_email

def get_all_orgaos():
    Session = sessionmaker(bind=db.run())
    with Session() as session:

        orgaos = session.query(Orgaos).all()
        if not orgaos:
            return []
    orgao = {o.nome: o.id for o in orgaos}
    return orgao


def compare_ghost_project_emails(ghost, projetos):
    filtered_ghost = [m for m in ghost if m['email'] not in projetos]
    return filtered_ghost

def create_users(dados):
    print("\n------------ Inserindo dados")
    Session = sessionmaker(bind=db.run())
    with Session() as session:
        for d in dados:
            # input("Digite algo para prosseguir!\n")
            config = definicoes[d['product_id']]
            
            # INSERT PROJETO
            projeto = Projetos(
                nome = d['bot_name'],
                cliente = d['product_id'],
                email = d['email'],
                qtd_termos = config['qtd_termos']
            )

            try:
                session.add(projeto)
                session.commit()
                print("-------------------")
                
                print(f"Projeto inserido: \nid: {projeto.id} \nbot_name: {d['bot_name']} \nemail: {d['email']} \nqtd_termos: {config['qtd_termos']} \nn_emails: {config['qtd_email']} \nproduct_id: {d['product_id']}")
                all_orgao = get_all_orgaos()
              
                print("-------------------")

                # INSERT ORGAO
                for orgao in config['orgao']:
                    orgao_id = all_orgao[orgao]
                    projetos_orgao = ProjetosHasOrgaos(
                        projetos_id = projeto.id,
                        orgaos_id = orgao_id
                    )
                    try:
                        session.add(projetos_orgao)
                        session.commit()
                        print(f"projetos_orgao inserido {orgao}")
                    except Exception as e:
                        print(f"Erro ao inserir o orgao {orgao}, no projeto de id {projeto.id}")
                        print(e)
                print("-------------------")   
                
                # TODO - Inserir mais de um email
                if config['qtd_email'] > 1:
                    print("Ainda não implementando, talvez chamar uma função!")

            except Exception as e:
                print("Erro ao Inserir Projeto ", str(e))


ghost_users = get_ghost_users()
projetos = get_all_projetos_email()

emails_filtrados = compare_ghost_project_emails(ghost_users, projetos)

create_users(emails_filtrados)

