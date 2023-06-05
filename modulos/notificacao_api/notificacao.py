
from modulos.notificacao_api.email.html import HTML

class SendNotification:
    def __init__(self, tramites, projeto):
        self.tramites = tramites
        self.projeto = projeto
        self.is_email = projeto.email_conf_id
        self.is_whatsapp = projeto.whatsapp_conf_id
        self.is_telegram = projeto.telegram_conf_id
        self.is_twitter = projeto.twitter_conf_id
        self.is_discord = projeto.discord_conf_id

    def verify_empty_tramites(self):
        count_empty = 0
        for key, value in self.tramites.items():
            if not value:
                count_empty += 1
        if count_empty == len(self.tramites):
            return True
        return False
    
    def execute(self):
        print(" - Enviando notificações:")
        print(self.tramites)
        
        print(f'\nWhatsapp: {self.is_whatsapp}')
        print(f'Telegram: {self.is_telegram}') 
        print(f'Twitter: {self.is_twitter}')
        print(f'Discord: {self.is_discord}')
        print(f'Email: {self.is_email}\n')
        
        if self.verify_empty_tramites():
            print(" - Nenhum tramite novo encontrado para notificar")
            return
        
        if self.is_email:
            print(" - Enviando email")
            HTML(self.is_email, self.tramites).execute()
        
        if self.is_whatsapp:
            print(" - Enviando whatsapp")
            pass
        
        if self.is_telegram:
            print(" - Enviando telegram")
            pass

        if self.is_twitter:
            print(" - Enviando twitter")
            pass

        if self.is_discord:
            print(" - Enviando discord")
            pass

        print(" - Notificações enviadas com sucesso")
        