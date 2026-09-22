from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status

from ..dependencies import get_catalog
from ..errors import ErrorRespuesta
from ..models import CompraCrear, Producto, ProductoActualizar, ProductoCrear
from ..notifications import notificar_compra
from ..repository import CatalogRepository

router = APIRouter(prefix="/productos", tags=["productos"])


@router.get(
    "",
    response_model=list[Producto],
    summary="Lista paginada del catálogo",
    description="R8: página pedida en el body y total de elementos en el header X-Total.",
)
async def listar_productos(
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    catalogo: CatalogRepository = Depends(get_catalog),
) -> list[Producto]:
    productos, total = await catalogo.listar(offset=offset, limit=limit)
    response.headers["X-Total"] = str(total)
    return productos


@router.get(
    "/{id}",
    response_model=Producto,
    summary="Obtener un producto",
    responses={404: {"model": ErrorRespuesta, "description": "Producto inexistente"}},
)
async def obtener_producto(
    id: int,
    catalogo: CatalogRepository = Depends(get_catalog),
) -> Producto:
    return await catalogo.obtener(id)


@router.post(
    "",
    response_model=Producto,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un producto",
)
async def crear_producto(
    payload: ProductoCrear,
    catalogo: CatalogRepository = Depends(get_catalog),
) -> Producto:
    return await catalogo.crear(payload)


@router.patch(
    "/{id}",
    response_model=Producto,
    summary="Actualizar un producto (parcial)",
    responses={404: {"model": ErrorRespuesta, "description": "Producto inexistente"}},
)
async def actualizar_producto(
    id: int,
    cambios: ProductoActualizar,
    catalogo: CatalogRepository = Depends(get_catalog),
) -> Producto:
    return await catalogo.actualizar(id, cambios)


@router.post(
    "/{id}/comprar",
    response_model=Producto,
    summary="Comprar unidades de un producto",
    responses={
        404: {"model": ErrorRespuesta, "description": "Producto inexistente"},
        409: {"model": ErrorRespuesta, "description": "Producto deshabilitado o stock insuficiente"},
    },
)
async def comprar_producto(
    id: int,
    compra: CompraCrear,
    background_tasks: BackgroundTasks,
    catalogo: CatalogRepository = Depends(get_catalog),
) -> Producto:
    """Compra con verificaciones concurrentes (R11) y notificación en 2.º plano (R13)."""
    producto = await catalogo.comprar(id, compra.cantidad)
    # R13: la notificación se dispara con la herramienta correcta del framework,
    # no con un asyncio.create_task suelto.
    background_tasks.add_task(notificar_compra, producto.id, compra.cantidad)
    return producto