# diretório contém todos os modelos de dados usando pydantic
# separando a estrutura de dados da lógica de negócio
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson import ObjectId

# Field para criar um alias das variaveis
# Config dict pra realizar as config internas do pydantic pro modelo
# pydantic permite definir a forma dos objetos, exigindo que os dados estajem em determinado formato
# o typing pra utilizar a tipagem opcional

# modelo de dados para um produto
class Product(BaseModel):
    id: Optional[ObjectId] = Field(None,alias='_id')
    name: str
    price: float
    description: Optional[str] = None
    stock: int
    
    model_config = ConfigDict(
        # permite que o modelo seja populado usando o alias '_id'
        populate_by_name = True,
        # permite que o pydantic trabalhe com tipos arbitrarios como o object id do Mongo
        arbitrary_types_allowed = True
    )

# classe para leitura de dados do DB e conversão em JSON
class ProductDBModel(Product):
    def model_dump(self, *, mode = 'python', include = None, exclude = None, context = None, by_alias = None, exclude_unset= False, exclude_defaults = False, exclude_none = False, round_trip=False, warnings = True, fallback = None, serialize_as_any = False):
        data = super().model_dump(mode = mode, include = include, exclude = exclude, context = context, by_alias = by_alias, exclude_unset= exclude_unset, exclude_defaults = exclude_defaults, exclude_none = exclude_none, round_trip=round_trip, warnings = warnings, fallback = fallback, serialize_as_any = serialize_as_any)
        if self.id:
            data['_id']= str(data['_id'])
        return data

class UpdateProduct(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = None    