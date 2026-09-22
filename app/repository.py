import asyncio
from decimal import Decimal

from .concurrency import ejecutar_en_paralelo
from .errors import ProductoNoEncontrado, ProductoNoHabilitado, StockInsuficiente
from .models import Producto, ProductoActualizar, ProductoCrear


class CatalogRepository:
    """Repositorio de productos en memoria (R2, R4).

    Regla general del TP: toda operación que toca el catálogo simula la
    consulta a la base con await asyncio.sleep(0.05) antes de tocar los datos
    en memoria. Por eso todos los métodos que acceden al catálogo son async
    def (R1) y ningún endpoint responde "instantáneamente".
    """

    def __init__(self) -> None:
        self._productos: dict[int, Producto] = {}
        self._proximo_id = 1
        self._cerrojo = asyncio.Lock()

    async def _simular_db(self) -> None:
        """Simula la latencia de una consulta a la base de datos."""
        await asyncio.sleep(0.05)

    async def _leer(self, id_producto: int) -> Producto:
        """Devuelve un producto o lanza ProductoNoEncontrado (R9)."""
        producto = self._productos.get(id_producto)
        if producto is None:
            raise ProductoNoEncontrado(f"No existe el producto con id {id_producto}.")
        return producto

    async def seed(self) -> None:
        """Carga el catálogo inicial con algunos productos de ejemplo."""
        await self._simular_db()
        iniciales = [
            ("Alfajor de maicena", Decimal("450.00"), 12, 0, True, "golosinas"),
            ("Gaseosa cola 500 ml", Decimal("1350.50"), 25, 2, True, "bebidas"),
            ("Caramelos surtidos", Decimal("300.00"), 40, 0, True, "golosinas"),
            ("Agua mineral 500 ml", Decimal("800.00"), 20, 0, False, "bebidas"),
            ("Chicles de menta", Decimal("250.00"), 10, 3, True, "golosinas"),
        ]
        for nombre, precio, stock, reservado, habilitado, categoria in iniciales:
            producto = Producto(
                id=self._proximo_id,
                nombre=nombre,
                precio=precio,
                stock=stock,
                stock_reservado=reservado,
                habilitado=habilitado,
                categoria=categoria,
            )
            self._productos[producto.id] = producto
            self._proximo_id += 1

    async def listar(self, offset: int = 0, limit: int = 10):
        """R8: devuelve la página pedida y el total de productos del catálogo."""
        await self._simular_db()
        todos = list(self._productos.values())
        total = len(todos)
        return todos[offset : offset + limit], total

    async def obtener(self, id_producto: int) -> Producto:
        await self._simular_db()
        return await self._leer(id_producto)

    async def crear(self, datos: ProductoCrear) -> Producto:
        await self._simular_db()
        producto = Producto(id=self._proximo_id, **datos.model_dump())
        self._productos[producto.id] = producto
        self._proximo_id += 1
        return producto

    async def actualizar(self, id_producto: int, cambios: ProductoActualizar) -> Producto:
        await self._simular_db()
        actual = await self._leer(id_producto)

        # R10: solo se aplican los campos que el cliente envió explícitamente.
        # model_dump(exclude_unset=True) conserva un null enviado a propósito
        # (p. ej. categoria: null) pero descarta un campo simplemente omitido.
        enviados = cambios.model_dump(exclude_unset=True)
        if not enviados:
            return actual

        combinado = Producto.model_validate({**actual.model_dump(), **enviados})
        self._productos[id_producto] = combinado
        return combinado

    async def _verificar_habilitado(self, producto: Producto) -> None:
        """Chequeo lento: simula un servicio remoto de habilitación."""
        await self._simular_db()
        if not producto.habilitado:
            raise ProductoNoHabilitado(f"El producto {producto.nombre} está deshabilitado.")

    async def _verificar_stock(self, producto: Producto, cantidad: int) -> None:
        """Chequeo lento: valida stock suficiente considerando reservados."""
        await self._simular_db()
        disponible = producto.stock - producto.stock_reservado
        if cantidad > disponible:
            raise StockInsuficiente(
                f"Stock insuficiente en {producto.nombre}: disponible {disponible}, pedido {cantidad}."
            )

    async def comprar(self, id_producto: int, cantidad: int) -> Producto:
        """R11 + R12: compra unidades de un producto.

        R11: habilitación y stock no dependen entre sí, así que se verifican en
        paralelo (ejecutar_en_paralelo), no una detrás de la otra.

        R12: la resta de stock ocurre dentro de un asyncio.Lock; si dos compras
        del mismo producto llegan al mismo tiempo, ninguna pisa a la otra.
        """
        # Regla general: simular la consulta antes de tocar datos.
        await self._simular_db()
        producto = await self._leer(id_producto)

        await ejecutar_en_paralelo(
            self._verificar_habilitado(producto),
            self._verificar_stock(producto, cantidad),
        )

        async with self._cerrojo:
            await self._simular_db()
            fresco = await self._leer(id_producto)
            if fresco.stock - cantidad < 0:
                raise StockInsuficiente(
                    f"Stock insuficiente en {fresco.nombre}: quedan {fresco.stock}, pedido {cantidad}."
                )
            fresco.stock -= cantidad
            return fresco