from pydantic import BaseModel, ConfigDict


class ServiceTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    price: int  # в дирамах (1 сомони = 100 дирам)
    currency: str
