from fastapi import BackgroundTasks
from loguru import logger
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from datetime import datetime  # ✅ Importação que faltava

from app.core.config.settings import settings


class EmailService:
    @staticmethod
    def get_mail_connection() -> ConnectionConfig:
        return ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )

    @staticmethod
    async def _send_mail(message: MessageSchema, conf: ConnectionConfig):
        """Método privado para o envio real do e-mail."""
        logger.info("--- TAREFA INICIADA: Tentando enviar e-mail. ---")
        try:
            fm = FastMail(conf)
            await fm.send_message(message)
            logger.success(f"E-mail enviado com sucesso para: {message.recipients}")
        except Exception as e:
            logger.error(f"FALHA AO ENVIAR e-mail para {message.recipients}. Erro: {e}")
            raise

    @staticmethod
    async def send_password_reset_email(email_to: str, token: str, background_tasks: BackgroundTasks):
        """
        Prepara e agenda o envio de um e-mail de redefinição de senha.
        """
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
        subject = "Redefinição de Senha - Buteco's Gestão"

        html_content = f"""
                <!DOCTYPE html>
                <html lang="pt-BR">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
                            margin: 0;
                            padding: 0;
                            background-color: #f4f4f7;
                            color: #333;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 20px auto;
                            background-color: #ffffff;
                            border-radius: 8px;
                            overflow: hidden;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                        }}
                        .header {{
                            background-color: #FFA500; /* Laranja Buteco's */
                            color: #ffffff;
                            padding: 24px;
                            text-align: center;
                        }}
                        .header h1 {{
                            margin: 0;
                            font-size: 24px;
                            font-weight: bold;
                        }}
                        .content {{
                            padding: 32px;
                            line-height: 1.6;
                        }}
                        .content p {{
                            margin: 0 0 16px;
                        }}
                        .button-container {{
                            text-align: center;
                            margin: 24px 0;
                        }}
                        .button {{
                            background-color: #0056b3; /* Azul mais escuro para melhor contraste */
                            color: #ffffff !important; /* ✅ Garante que o texto seja branco */
                            padding: 14px 28px;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                            display: inline-block;
                        }}
                        .footer {{
                            background-color: #f4f4f7;
                            padding: 20px;
                            text-align: center;
                            font-size: 12px;
                            color: #777;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Buteco's Gestão</h1>
                        </div>
                        <div class="content">
                            <h2>Olá,</h2>
                            <p>Recebemos uma solicitação para redefinir a senha da sua conta. Se foi você, clique no botão abaixo para prosseguir.</p>
                            <div class="button-container">
                                <a href="{reset_url}" target="_blank" class="button">Redefinir Minha Senha</a>
                            </div>
                            <p>Se você não fez essa solicitação, pode ignorar este e-mail com segurança. Nenhuma alteração será feita na sua conta.</p>
                            <p>Este link de redefinição de senha expirará em <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos</strong>.</p>
                            <br>
                            <p>Atenciosamente,</p>
                            <p><strong>Equipe Buteco's</strong></p>
                        </div>
                        <div class="footer">
                            <p>&copy; {datetime.now().year} Buteco's Gestão. Todos os direitos reservados.</p>
                            <p>Timon, Maranhão, Brasil</p>
                        </div>
                    </div>
                </body>
                </html>
                """

        message = MessageSchema(
            subject=subject,
            recipients=[email_to],
            body=html_content,
            subtype="html"
        )

        conf = EmailService.get_mail_connection()

        # Mantendo em modo de depuração. Descomente a linha de baixo para usar background tasks.
        logger.warning("MODO DE DEPURAÇÃO: Enviando e-mail no fluxo principal para capturar erros.")
        await EmailService._send_mail(message, conf)
        # background_tasks.add_task(EmailService._send_mail, message, conf)


# Instância global do serviço
email_service = EmailService()
