import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
load_dotenv()

class Email:

    def ses(template, email_addr):
        print("SES-------------")
        SMTP_USER = os.getenv("SMTP_USER")
        SMTP_PASSWD = os.getenv("SMTP_PASSWD")
        SMTP_SENDER = os.getenv("SMTP_SENDER")
        SMTP_SERVER = os.getenv("SMTP_SERVER")
        SMTP_PORT = os.getenv("SMTP_PORT")
        print( "email_addr", email_addr)
        # print( "SMTP_USER", SMTP_USER)
        # print( "SMTP_PASSWD", SMTP_PASSWD)
        # print( "SMTP_SENDER", SMTP_SENDER)
        # print( "SMTP_SERVER", SMTP_SERVER)
        # print( "SMTP_PORT", SMTP_PORT)
    
        # print( "template len", len(template))
        dia_atual_string = datetime.now().strftime("%d/%m/%Y")

        from_address = SMTP_SENDER
        from_address = "Nucleo <{}>".format(from_address)
        to_address = email_addr

        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = to_address
        msg['Subject'] = "Seu relátorio LegislaTech! " + dia_atual_string


        msg.attach(MIMEText(template, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))
        server.starttls()

        server.login(SMTP_USER, SMTP_PASSWD)
        text = msg.as_string()
        server.sendmail(from_address, to_address, text)
        print("\n\n\n------Email enviado com sucesso!")
        server.quit()

    def sendy(template, email):
        print("Sendy-------------")
        headers = {}

        dia_atual_string = datetime.now().strftime("%d/%m/%Y")
        hora_minuto_atual_brasil = datetime.now(timezone('America/Sao_Paulo')).strftime("%H:%M")
        subject = email.email_subject + " - " + dia_atual_string + " - " + hora_minuto_atual_brasil

        files = {
            'api_key': (None, email.sendy_token),
            'from_name': (None, email.email_name),
            'from_email': (None, email.email_sender),
            'reply_to': (None, email.email_sender),
            'title': (None, email.notification_title),
            'subject': (None, subject),
            'html_text': (None, template),
            'brand_id': (None, email.sendy_brand_id),
            'send_campaign': (None, '1'),
            'list_ids': (None, email.sendy_list_id),
            'track_opens': (None, '1'),
            'track_clicks': (None, '1'),
        }

        response = requests.post(email.sendy_endpoint, headers=headers, files=files)
        print(f'Email enviado com sucesso')
        print(response.status_code)
        print(response.text)