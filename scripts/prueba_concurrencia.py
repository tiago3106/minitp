"""Evidencia de R11 + R12: dispara varias compras del MISMO producto al mismo tiempo.

Probá los capítulos 3 así:
  R11 (verificaciones concurrentes): las 8 compras terminan sin errores
      y el tiempo total queda cerca de "verificación + resta", no de 8 veces.
  R12 (sin condiciones de carrera): el stock final debe ser exactamente
      el inicial menos la suma de todas las cantidades compradas.

Uso: con el servidor corriendo (python run.py), en otra terminal:

    python scripts/prueba_concurrencia.py [n_compras]
"""

import asyncio
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8000"
STOCK_INICIAL = 10
CANTIDAD = 1


async def comprar(cliente: httpx.AsyncClient, id_producto: int, cantidad: int) -> httpx.Response:
    return await cliente.post(f"{BASE_URL}/productos/{id_producto}/comprar", json={"cantidad": cantidad})


async def principal() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    async with httpx.AsyncClient(timeout=30) as cliente:
        creado = await cliente.post(
            f"{BASE_URL}/productos",
            json={
                "nombre": "Chocolate de las rutinas",
                "precio": "320.00",
                "stock": STOCK_INICIAL,
                "stock_reservado": 0,
                "habilitado": True,
                "categoria": "golosinas",
            },
        )
        creado.raise_for_status()
        id_producto = creado.json()["id"]
        print(f"Producto creado: id={id_producto} | stock inicial={STOCK_INICIAL}")

        inicio = time.perf_counter()
        respuestas = await asyncio.gather(
            *(comprar(cliente, id_producto, CANTIDAD) for _ in range(n))
        )
        duracion = time.perf_counter() - inicio

        exitosas = [r for r in respuestas if r.status_code == 200]
        con_error = [r for r in respuestas if r.status_code != 200]

        print(f"\nCompras disparadas a la vez: {n} | exitosas: {len(exitosas)} | con error: {len(con_error)}")
        print(f"Tiempo total de las {n} compras concurrentes: {duracion:.3f} s")
        if con_error:
            for r in con_error:
                print("  error:", r.status_code, r.json())
                return

        stock = (await cliente.get(f"{BASE_URL}/productos/{id_producto}")).json()["stock"]
        esperado = STOCK_INICIAL - n * CANTIDAD
        print(f"\nStock final: {stock} (esperado: {esperado})")
        if stock == esperado:
            print("R12 OK: sin condiciones de carrera, ninguna compra pisó a otra.")
        else:
            print("R12 FALLÓ: hubo una actualización perdida.")


if __name__ == "__main__":
    asyncio.run(principal())