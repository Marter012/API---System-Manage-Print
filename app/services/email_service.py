from email.message import EmailMessage

import aiosmtplib

from app.config.settings import settings


class EmailService:

    async def send_password_reset_code(self, recipient, code):

        message = EmailMessage()

        message["From"] = settings.SMTP_FROM
        message["To"] = recipient
        message["Subject"] = "Código para recuperar tu contraseña"

        message.set_content(
            f"""
Hola,

Recibimos una solicitud para cambiar tu contraseña.

Tu código de recuperación es:

{code}

Este código es válido durante 10 minutos.

Si no solicitaste cambiar tu contraseña, ignora este mensaje.

Saludos,
Boutique de Sabores
"""
        )
        print("SMTP HOST:", settings.SMTP_HOST)
        print("SMTP PORT:", settings.SMTP_PORT)
        print("SMTP USER:", settings.SMTP_USERNAME)
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )