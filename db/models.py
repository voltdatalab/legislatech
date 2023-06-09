from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Projetos(Base):
    __tablename__ = 'projetos'
    id = Column(Integer, primary_key=True)
    nome = Column(Text)
    cliente = Column(Text)
    email = Column(Text)
    openai_token = Column(Text)
    shlink_token = Column(Text)
    
    email_conf_id = Column(Integer, ForeignKey('email_conf.id'))
    whatsapp_conf_id = Column(Integer, ForeignKey('whatsapp_conf.id'))
    telegram_conf_id = Column(Integer, ForeignKey('telegram_conf.id'))
    twitter_conf_id = Column(Integer, ForeignKey('twitter_conf.id'))
    discord_conf_id = Column(Integer, ForeignKey('discord_conf.id'))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return "<Projetos(id='%s', nome='%s', cliente='%s', openai_token='%s', shlink_token='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (self.id, self.nome, self.cliente, self.openai_token, self.shlink_token, self.created_at, self.updated_at, self.deleted_at)

class EmailConf(Base):
    __tablename__ = 'email_conf'
    id = Column(Integer, primary_key=True)

    email_name = Column(Text)
    email_sender = Column(Text)
    email_subject = Column(Text)

    notification_title = Column(Text)
    notification_intro = Column(Text)
    banner = Column(Text)
    logo = Column(Text) 
    footer = Column(Text)
    footer_sub = Column(Text)
    link_privacy = Column(Text)

    html_template = Column(Text)

    sendy_brand_id = Column(Text)
    sendy_list_id = Column(Text)
    sendy_endpoint = Column(Text) 
    sendy_token = Column(Text) 

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<EmailConf(id='%s', email_name='%s', email_sender='%s', email_subject='%s', notification_title='%s', notification_intro='%s', banner='%s', footer='%s', footer_sub='%s', link_privacy='%s', html_template='%s', sendy_brand_id='%s', sendy_list_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (self.id, self.email_name, self.email_sender, self.email_subject, self.notification_title, self.notification_intro, self.banner, self.footer, self.footer_sub, self.link_privacy, self.html_template, self.sendy_brand_id, self.sendy_list_id, self.created_at, self.updated_at, self.deleted_at)

class WhatsAppConf(Base):
    __tablename__ = 'whatsapp_conf'
    id = Column(Integer, primary_key=True)
    token = Column(Text)
    chat_id = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<WhatsAppConf(id='%s', token='%s', chat_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (self.id, self.token, self.chat_id, self.created_at, self.updated_at, self.deleted_at)

class TelegramConf(Base):
    __tablename__ = 'telegram_conf'
    id = Column(Integer, primary_key=True)
    token = Column(Text)
    chat_id = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<TelegramConf(id='%s', token='%s', chat_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (self.id, self.token, self.chat_id, self.created_at, self.updated_at, self.deleted_at)

class TwitterConf(Base):
    __tablename__ = 'twitter_conf'
    id = Column(Integer, primary_key=True)
    consumer_key = Column(Text)
    consumer_secret = Column(Text)
    access_key = Column(Text)
    access_secret = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<TwitterConf(id='%s', consumer_key='%s', consumer_secret='%s', access_key='%s', access_secret='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (self.id, self.consumer_key, self.consumer_secret, self.access_key, self.access_secret, self.created_at, self.updated_at, self.deleted_at)

class DiscordConf(Base):
    __tablename__ = 'discord_conf'
    id = Column(Integer, primary_key=True)
    token = Column(Text)
    chat_id = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<DiscordConf(id='%s', token='%s', chat_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (self.id, self.token, self.chat_id, self.created_at, self.updated_at, self.deleted_at)


class Termos(Base):
    __tablename__ = 'termos'
    id = Column(Integer, primary_key=True)
    nome = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return "<Termos(id='%s', nome='%s', created_at='%s', deleted_at='%s', updated_at='%s')>" % (
            self.id, self.nome, self.created_at, self.deleted_at, self.updated_at)
    
class Categorias(Base):
    __tablename__ = 'categorias'
    id = Column(Integer, primary_key=True)
    nome = Column(Text)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return "<Categorias(id='%s', nome='%s', updated_at='%s', created_at='%s', deleted_at='%s', prioridade='%s')>" % (
            self.id, self.nome, self.updated_at, self.created_at, self.deleted_at, self.prioridade)

class Orgaos(Base):
    __tablename__ = 'orgaos'
    id = Column(Integer, primary_key=True)
    nome = Column(Text)
    descricao = Column(Text)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return "<Orgaos(id='%s', nome='%s', updated_at='%s', created_at='%s', deleted_at='%s')>" % (
            self.id, self.nome, self.updated_at, self.created_at, self.deleted_at)

class Tramites(Base):
    __tablename__ = 'tramites'
    id = Column(Integer, primary_key=True)
    orgaos_id = Column(Integer, ForeignKey('orgaos.id'))
    resumo = Column(Text)
    resumo_ia = Column(Text)
    data_origem = Column(Text)
    autores = Column(Text)
    link_pdf = Column(Text)
    link_web = Column(Text)
    hashing = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime)

    def __repr__(self):
        return "<Tramites(id='%s', resumo='%s', data_origem='%s', autores='%s', link_pdf='%s', link_web='%s', created_at='%s', updated_at='%s', deleted_at='%s', orgaos_id='%s')>" % (
            self.id, self.resumo, self.data_origem, self.autores, self.link_pdf, self.link_web, self.created_at, self.updated_at, self.deleted_at, self.orgaos_id)

class TramiteDetalhes(Base):
    __tablename__ = 'tramite_detalhes'
    id = Column(Integer, primary_key=True)
    json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime)
    tramites_id = Column(Integer, ForeignKey('tramites.id'))

    def __repr__(self):
        return "<TramiteDetalhes(id='%s', json='%s', created_at='%s', updated_at='%s', deleted_at='%s', tramites_id='%s')>" % (
            self.id, self.json, self.created_at, self.updated_at, self.deleted_at, self.tramites_id)

class ProjetosHasTramites(Base):
    __tablename__ = 'projetos_has_tramites'
    email = Column(Boolean)
    whatsapp = Column(Boolean)
    telegram = Column(Boolean)
    twitter = Column(Boolean)
    discord = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime)
    tramites_id = Column(Integer, ForeignKey('tramites.id'), primary_key=True)
    projetos_id = Column(Integer, ForeignKey('projetos.id'), primary_key=True)

    def __repr__(self):
        return "<ProjetosHasTramites(email='%s', whatsapp='%s', telegram='%s', twitter='%s', created_at='%s', updated_at='%s', deleted_at='%s', tramites_id='%s', projetos_id='%s')>" % (
            self.email, self.whatsapp, self.telegram, self.twitter, self.created_at, self.updated_at, self.deleted_at, self.tramites_id, self.projetos_id)

class ProjetosHasOrgaos(Base):
    __tablename__ = 'projetos_has_orgaos'
    projetos_id = Column(Integer, ForeignKey('projetos.id'), primary_key=True)
    orgaos_id = Column(Integer, ForeignKey('orgaos.id'), primary_key=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())   
    deleted_at = Column(DateTime)

    def __repr__(self):
        return "<ProjetosHasOrgaos(projetos_id='%s', orgaos_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (
            self.projetos_id, self.orgaos_id, self.created_at, self.updated_at, self.deleted_at)    
    
class TramitesHasTermos(Base):
    __tablename__ = 'tramites_has_termos'
    tramites_id = Column(Integer, ForeignKey('tramites.id'), primary_key=True)
    termos_id = Column(Integer, ForeignKey('termos.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(Text)

    def __repr__(self):
        return "<TramitesHasTermos(tramites_id='%s', termos_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (
            self.tramites_id, self.termos_id, self.created_at, self.updated_at, self.deleted_at)
    
class ProjetosHasTermos(Base):
    __tablename__ = 'projetos_has_termos'
    projetos_id = Column(Integer, ForeignKey('projetos.id'), primary_key=True)
    termos_id = Column(Integer, ForeignKey('termos.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(Text)

    def __repr__(self):
        return "<ProjetosHasTermos(projetos_id='%s', termos_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (
            self.projetos_id, self.termos_id, self.created_at, self.updated_at, self.deleted_at)

class TermosHasCategorias(Base):
    __tablename__ = 'termos_has_categorias'
    termos_id = Column(Integer, ForeignKey('termos.id'), primary_key=True)
    categorias_id = Column(Integer, ForeignKey('categorias.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(Text)

    def __repr__(self):
        return "<TermosHasCategorias(termos_id='%s', categorias_id='%s', created_at='%s', updated_at='%s', deleted_at='%s')>" % (
            self.termos_id, self.categorias_id, self.created_at, self.updated_at, self.deleted_at)  