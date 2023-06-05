# import os
import requests
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from datetime import datetime
from pytz import timezone
# import pytz

# def send_ses(email_addr, template):
    # from_address = os.getenv('EMAIL_SENDER')
    # from_address = "Reset <{}>".format(from_address)
    # to_address = email_addr

    # msg = MIMEMultipart()
    # msg['From'] = from_address
    # msg['To'] = to_address
    # msg['Subject'] = os.getenv('EMAIL_SUB')


    # msg.attach(MIMEText(template, 'html'))

    # server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
    # server.starttls()

    # server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWD'))
    # text = msg.as_string()
    # server.sendmail(from_address, to_address, text)
    # print("\n\n\n------Email enviado com sucesso!")
    # server.quit()
class Email:

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