from fastapi import Request

from .repository import CatalogRepository


def get_catalog(request: Request) -> CatalogRepository:
    """R2: entrega el repositorio de productos por inyección de dependencias.

    El repositorio se creó una sola vez en el lifespan (R4) y vive en
    app.state; los handlers nunca importan una variable global suelta.
    """
    return request.app.state.catalogo