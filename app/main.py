from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .errors import ErrorDominio
from .repository import CatalogRepository
from .routers import comparacion, productos


@asynccontextmanager
async def lifespan(app: FastAPI):
    # R4: el repositorio (el catálogo) se crea UNA sola vez en el lifespan,
    # no en cada pedido.
    app.state.catalogo = CatalogRepository()
    await app.state.catalogo.seed()
    yield


app = FastAPI(
    title="Mini TP — Kiosco: un catálogo con compras",
    description="Integrador de los capítulos 1 a 3 de Programación III (TUP, UTN FRM).",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ErrorDominio)
async def manejar_error_dominio(_: Request, exc: ErrorDominio) -> JSONResponse:
    """R9: los errores del dominio responden con formato propio y estable."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"codigo": exc.codigo, "mensaje": exc.mensaje}},
    )


app.include_router(productos.router)
app.include_router(comparacion.router)