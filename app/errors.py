from pydantic import BaseModel


class ErrorDominio(Exception):
    """Error de negocio del kiosco con formato de respuesta propio y estable (R9).

    No se usa el {"detail": ...} por defecto de FastAPI: cada error de dominio
    responde con {"error": {"codigo": ..., "mensaje": ...}}.
    """

    codigo: str = "ERROR_DOMINIO"
    status_code: int = 400

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje

    def __str__(self) -> str:
        return self.mensaje


class ProductoNoEncontrado(ErrorDominio):
    codigo = "PRODUCTO_NO_ENCONTRADO"
    status_code = 404


class ProductoNoHabilitado(ErrorDominio):
    codigo = "PRODUCTO_NO_HABILITADO"
    status_code = 409


class StockInsuficiente(ErrorDominio):
    codigo = "STOCK_INSUFICIENTE"
    status_code = 409


class ErrorBody(BaseModel):
    codigo: str
    mensaje: str


class ErrorRespuesta(BaseModel):
    error: ErrorBody