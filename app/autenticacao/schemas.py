from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, BeforeValidator, StringConstraints

def normalizar_email(valor: str) -> str:
    return valor.strip().lower()

EmailNormalizado = Annotated[
    EmailStr,
    BeforeValidator(normalizar_email)
]

StringNaoVazia = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1
    )
]

class RegisterInput(BaseModel):
    nome: StringNaoVazia = Field(min_length=6, max_length=50)
    email: EmailNormalizado = Field(max_length=100)
    senha: str = Field(min_length=8, max_length=255)


class LoginInput(BaseModel):
    email: EmailNormalizado = Field(max_length=100)
    senha: str = Field(max_length=255)