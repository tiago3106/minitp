# Mini TP — Kiosco: un catálogo con compras

Integrador de los capítulos 1 a 3 de Programación III (TUP · UTN FRM):
fundamentos de FastAPI / ASGI, contratos con Pydantic y ejecución asincrónica.
Un único dominio (Producto) en memoria: sin base de datos, sin auth y sin Redis.

## Requisitos

- Python 3.10 o superior
- `pip`

## Instalación y ejecución

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python run.py                   # o: uvicorn app.main:app --reload
```

La API queda en <http://127.0.0.1:8000>. La documentación interactiva
(con los esquemas reales de cada respuesta, R3) está en
<http://127.0.0.1:8000/docs>.

Al arrancar, el lifespan crea el catálogo una sola vez (R4) y lo carga con
productos de ejemplo.

## Endpoints

| Método y ruta                    | Parámetros                             | Devuelve                                          |
| -------------------------------- | -------------------------------------- | ------------------------------------------------- |
| `GET /productos`                 | query: `offset` (0), `limit` (10)      | lista de Producto; total en header `X-Total` (R8) |
| `GET /productos/{id}`            | path: `id`                             | un Producto o error 404 normado                   |
| `POST /productos`                | body: `ProductoCrear`                  | el Producto creado (201)                          |
| `PATCH /productos/{id}`          | path: `id` · body: `ProductoActualizar`| el Producto actualizado (R10)                     |
| `POST /productos/{id}/comprar`   | path: `id` · body: `CompraCrear`       | el Producto con el stock ya descontado            |
| `GET /comparacion/sincrono`      | —                                      | `resultados` + `duracion_ms` (versión bloqueante) |
| `GET /comparacion/asincrono`     | —                                      | `resultados` + `duracion_ms` (versión concurrente)|

Ejemplo de error de dominio (formato propio, R9):

```json
{
  "error": { "codigo": "STOCK_INSUFICIENTE", "mensaje": "..." }
}
```

## Cómo se cumple cada requisito

### Capítulo 1 — fundamentos (R1 a R4)
- **R1** — Todos los handlers y todos los métodos que acceden al catálogo están
  declarados con `async def` (`app/repository.py`, handlers en `app/routers/`).
- **R2** — El catálogo se inyecta en cada handler con `Depends(get_catalog)`
  (`app/dependencies.py`); no hay ninguna variable global suelta.
- **R3** — Todos los endpoints declaran `response_model` explícito.
- **R4** — El repositorio se crea una sola vez en el `lifespan` de
  `app/main.py` y vive en `app.state`.

### Capítulo 2 — contratos (R5 a R10)
- **R5** — Tres modelos distintos: `ProductoCrear`, `ProductoActualizar` y
  `Producto` (lectura).
- **R6** — El precio es `Decimal`, nunca `float` (`Field(gt=0)`).
- **R7** — Validación de un campo con `Field` (precio, stock, etc.) y
  validación de dos campos con `@model_validator`: `stock_reservado <= stock`.
- **R8** — `GET /productos` pagina con `offset`/`limit` y el total viaja en el
  header `X-Total` (no en un campo del body, para no anidar modelos).
- **R9** — Los errores del dominio responden con `{error: {codigo, mensaje}}`
  (ver `app/errors.py` y el handler en `app/main.py`).
- **R10** — `PATCH` usa `model_dump(exclude_unset=True)`: un campo omitido no
  se toca; un campo enviado como `null` (p. ej. `categoria: null`) sí.

### Capítulo 3 — asincronismo (R11 a R14)
- **R11** — Al comprar, habilitación y stock se verifican en paralelo con
  `asyncio.gather` (ambas hacen `asyncio.sleep(0.05)` y ninguna depende de la
  otra) — `app/concurrency.py` y `CatalogRepository.comprar`.
- **R12** — La resta de stock ocurre dentro de un `asyncio.Lock`, así que dos
  compras simultáneas del mismo producto no se pisan entre sí.
- **R13** — La notificación de compra confirmada se dispara con
  `BackgroundTasks`, la herramienta del framework (`app/notifications.py`).
- **R14** — `GET /comparacion/sincrono` vs. `GET /comparacion/asincrono`
  devuelven `duracion_ms` reales (~150 ms contra ~50 ms con 3 verificaciones).

### Regla general
Toda operación que toca el catálogo simula la consulta a la base con
`await asyncio.sleep(0.05)` antes de tocar los datos en memoria.

## Evidencia de R11 y R12 bajo concurrencia real

Con el servidor corriendo:

```bash
python scripts/prueba_concurrencia.py
```

El script dispara 8 compras del mismo producto **al mismo tiempo** con
`asyncio.gather` (no con un `for` de curl, que las desincroniza) y muestra:
- el tiempo total de las 8 compras concurrentes;
- que todas terminan sin errores (R11);
- que el stock final coincide con lo esperado, sin actualizaciones perdidas (R12).

## Rúbrica

| Bloque                                  | Puntos |
| --------------------------------------- | ------ |
| Capítulo 1 — fundamentos (R1–R4)        | 20     |
| Capítulo 2 — contratos (R5–R10)         | 40     |
| Capítulo 3 — asincronismo (R11–R14)     | 30     |
| Calidad general (módulos, nombres, README) | 10  |