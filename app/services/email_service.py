import httpx

from app.config.settings import settings


class EmailService:

    async def send_password_reset_code(
        self,
        recipient: str,
        code: str,
    ) -> None:

        url = "https://api.mailersend.com/v1/email"

        headers = {
            "Authorization": (
                f"Bearer {settings.MAILERSEND_API_KEY}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "from": {
                "email": settings.MAILERSEND_FROM_EMAIL,
                "name": "Boutique de Sabores",
            },
            "to": [
                {
                    "email": recipient,
                }
            ],
            "subject": "Código para recuperar tu contraseña",
            "text": (
                "Hola,\n\n"
                "Recibimos una solicitud para cambiar "
                "tu contraseña.\n\n"
                "Tu código de recuperación es:\n\n"
                f"{code}\n\n"
                "Este código es válido durante 10 minutos.\n\n"
                "Si no solicitaste cambiar tu contraseña, "
                "ignorá este mensaje.\n\n"
                "Saludos,\n"
                "Boutique de Sabores"
            ),
        }

        async with httpx.AsyncClient() as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=30.0,
            )

            response.raise_for_status()
