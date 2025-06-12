import re
from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException


def validar_telefone(telefone: str):
    # Exemplo simples: permite números com DDD e opcional +, espaços, parênteses, hífen
    pattern = re.compile(r'^\+?[\d\s\-\(\)]{8,15}$')
    if not pattern.match(telefone):
        raise HTTPException(status_code=400, detail="Telefone em formato inválido")

def validar_email(email: str):
    try:
        valid = validate_email(email)
        return valid.email  # email normalizado
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=f"E-mail inválido: {str(e)}")