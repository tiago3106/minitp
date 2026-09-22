import asyncio
from typing import Awaitable

from .errors import ErrorDominio


async def ejecutar_en_paralelo(*coros: Awaitable) -> list:
    """Ejecuta verificaciones independientes en paralelo (R11 y R14).

    Las tareas no dependen entre sí, así que corren concurrentes en vez de una
    detrás de la otra. Usa asyncio.gather (compatible con Python 3.10) con
    return_exceptions para poder re-lanzar un ErrorDominio aislado: de otro
    modo gather envolvería el error y el handler normado (R9) no lo atraparía.
    """
    resultados = await asyncio.gather(*coros, return_exceptions=True)

    primer_error = next(
        (r for r in resultados if isinstance(r, ErrorDominio)),
        None,
    )
    if primer_error is not None:
        raise primer_error

    for r in resultados:
        if isinstance(r, BaseException):
            raise r

    return list(resultados)