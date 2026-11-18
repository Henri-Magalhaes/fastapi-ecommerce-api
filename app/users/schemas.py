from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime

from app.users.models import RoleEnum
from app.autenticacao.schemas import EmailNormalizado, StringNaoVazia
from app.pedidos.schemas import PedidoResponse

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: StringNaoVazia
    email: StringNaoVazia
    dt_criacao: datetime

class UsuarioPaginatedResponse(BaseModel):
    limit: int = Field(gt=0, le=100, default=15)
    offset: int = Field(ge=0, default=0)
    role: RoleEnum = Field(default=RoleEnum.CLIENTE)

class UserUpdate(BaseModel):
    nome: StringNaoVazia | None = Field(min_length=6, max_length=50, default=None)
    email: EmailNormalizado | None = Field(max_length=100, default=None)

    @model_validator(mode="before")
    @classmethod
    def validar_dados(cls, data):
        if isinstance(data, dict):
            for campo, valor in data.items():
                if valor is None:
                    raise ValueError(
                        f"O campo {campo} não pode ser nulo"
                    )

        return data

class UserRoleUpdate(BaseModel):
    role: RoleEnum

class UserPedidosResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    nome: StringNaoVazia
    email: StringNaoVazia
    pedidos: list[PedidoResponse]