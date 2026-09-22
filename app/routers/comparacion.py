import asyncio
import time

from fastapi import APIRouter

from ..concurrency import ejecutar_en_paralelo
from ..models import ComparacionRespuesta

router = APIRouter(prefix="/comparacion", tags=["comparación"])

VERIFICACIONES = ("habilitado", "stock", "precio")


async def _verificacion_simulada(etiqueta: str) -> str:
    """Simula una verificación que tarda 50 ms, como un chequeo remoto."""
    await asyncio.sleep(0.05)
    return f"verificación '{etiqueta}': ok"


@router.get(
    "/sincrono",
    response_model=ComparacionRespuesta,
    summary="Variaciones secuenciales",
    description="R14: las mismas verificaciones corridas una detrás de la otra (≈ 150 ms).",
)
async def comparacion_sincrona() -> ComparacionRespuesta:
    inicio = time.perf_counter()
    resultados = [await _verificacion_simulada(v) for v in VERIFICACIONES]
    duracion_ms = (time.perf_counter() - inicio) * 1000
    return ComparacionRespuesta(resultados=resultados, duracion_ms=round(duracion_ms, 2))


@router.get(
    "/asincrono",
    response_model=ComparacionRespuesta,
    summary="Variaciones concurrentes",
    description="R14: las mismas verificaciones en paralelo (≈ 50 ms).",
)
async def comparacion_asincrona() -> ComparacionRespuesta:
    inicio = time.perf_counter()
    resultados = await ejecutar_en_paralelo(
        *(_verificacion_simulada(v) for v in VERIFICACIONES)
    )
    duracion_ms = (time.perf_counter() - inicio) * 1000
    return ComparacionRespuesta(resultados=resultados, duracion_ms=round(duracion_ms, 2))