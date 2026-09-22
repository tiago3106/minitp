from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ProductoBase(BaseModel):
    """Campos compartidos por los modelos del producto."""

    nombre: str = Field(min_length=1, description="Nombre del producto.")
    precio: Decimal = Field(gt=Decimal("0"), description="Precio unitario. Siempre Decimal, nunca float (R6).")
    stock: int = Field(ge=0, description="Stock total disponible.")
    stock_reservado: int = Field(default=0, ge=0, description="Unidades reservadas. No puede superar a stock.")
    habilitado: bool = Field(default=True, description="Si está habilitado para la venta.")
    categoria: Optional[str] = Field(default=None, description="Categoría opcional.")

    @model_validator(mode="after")
    def _stock_reservado_no_supera_stock(self) -> "ProductoBase":
        """Validación que involucra dos campos del mismo modelo (R7)."""
        if self.stock_reservado > self.stock:
            raise ValueError("stock_reservado no puede superar a stock.")
        return self


class ProductoCrear(ProductoBase):
    """Payload para crear un producto (R5)."""


class Producto(ProductoBase):
    """Esquema que se devuelve al leer un producto: agrega el id asignado por el servidor (R5)."""

    id: int


class ProductoActualizar(BaseModel):
    """Payload de PATCH: todos los campos son opcionales (R5).

    Un campo que no se envía NO aparece en model_fields_set; un campo enviado
    explícitamente como null sí aparece. Esa distinción la usa el repositorio
    para cumplir R10.
    """

    nombre: Optional[str] = Field(default=None, min_length=1)
    precio: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    stock: Optional[int] = Field(default=None, ge=0)
    stock_reservado: Optional[int] = Field(default=None, ge=0)
    habilitado: Optional[bool] = None
    categoria: Optional[str] = None


class CompraCrear(BaseModel):
    """Payload de la compra de un producto."""

    cantidad: int = Field(ge=1, description="Cantidad de unidades a comprar.")


class ComparacionRespuesta(BaseModel):
    """Resultado del endpoint de comparación síncrono/asíncrono (R14)."""

    resultados: list[str]
    duracion_ms: float