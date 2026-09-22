import asyncio


async def notificar_compra(id_producto: int, cantidad: int) -> None:
    """Simula el envío de una notificación de compra confirmada (R13).

    Corre como tarea en segundo plano con BackgroundTasks (la herramienta del
    framework), no con un asyncio.create_task suelto del que nadie se ocupa.
    """
    await asyncio.sleep(0.1)
    print(f"[notificación] Compra confirmada: {cantidad} unidad(es) del producto {id_producto}.")