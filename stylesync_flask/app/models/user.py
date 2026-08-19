from pydantic import BaseModel

# modelo de dados para um usuario
class LoginPayload(BaseModel):
    username: str
    password: str