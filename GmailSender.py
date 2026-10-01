import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Конфигурация
GMAIL_SENDER = "bestgrammautorisation@gmail.com"  # Ваш Gmail надо сделать чтото там подозрительный источник
GMAIL_PASSWORD = "ckmu aluo bzke lqjn"  # Пароль или App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_gmail(email,psw):
    try:
        # Создание сообщения
        msg = MIMEMultipart()
        msg['From'] = GMAIL_SENDER
        msg['To'] = email
        msg['Subject'] = "BESTgramm registration"

        # Добавление текста письма
        message_body = f"""
Hello there!!
Your email was specified during registration in our service, if it was you, here is your password:
___  {psw}  ___
If it wasn't you, don't tell this password to anyone
        """
        msg.attach(MIMEText(message_body, 'plain'))

        # Отправка через SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_PASSWORD)
            server.send_message(msg)

        return "success"

    except smtplib.SMTPAuthenticationError:
        return "autification error"
    except Exception as e:
        return f"send error: {str(e)}"
