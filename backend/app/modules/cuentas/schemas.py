from pydantic import BaseModel, EmailStr, Field


class RegistroIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    acepta_terminos: bool


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PinIn(BaseModel):
    pin: str = Field(pattern=r"^\d{4,6}$")


class PinSetIn(PinIn):
    password: str = Field(max_length=128)  # se pide la contraseña para cambiar el PIN


class UsuarioOut(BaseModel):
    id: str
    email: str
    rol: str