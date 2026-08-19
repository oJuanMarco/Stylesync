from pydantic import BaseModel, ConfigDict
from datetime import date

# modelo de dados para uma venda
class Sale(BaseModel):
    sale_date: date
    product_id: str
    quantify: int
    total_value: float

    model_config = ConfigDict(
        # permite que o modelo seja populado usando o alias '_id'
        populate_by_name = True,
        # permite que o pydantic trabalhe com tipos arbitrarios como o object id do Mongo
        arbitrary_types_allowed = True
    )