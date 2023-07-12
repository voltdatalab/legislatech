from models import *
import conn as conn
from sqlalchemy.orm import sessionmaker

engine = conn.run()

tables = [
    DiscordConf,
    WhatsAppConf,
    EmailConf,
    TwitterConf,
    TelegramConf,
    Projetos,
    Termos,
    Categorias,
    Orgaos,
    Tramites,
    TramiteDetalhes,
    ProjetosHasTramites,
    TramitesHasTermos,
    ProjetosHasTermos,
    ProjetosHasOrgaos,
    TermosHasCategorias,
    Periodicidade
]
for table in tables:
    table.__table__.create(bind=engine, checkfirst=True)

session = sessionmaker(bind=engine)()
orgaos = [
        Orgaos(nome='dou',descricao='Diário Oficial da União'),
        Orgaos(nome='camara',descricao='Câmara dos Deputados'),
        Orgaos(nome='senado',descricao='Senado Federal'),
    ]

session.add_all(orgaos)
session.commit()
session.close()
