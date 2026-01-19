from piccolo.table import Table


class HookIndexing:

    @staticmethod
    async def create(row: Table) -> Table:
        raise NotImplementedError("Product creation indexing not implemented")

    @staticmethod
    async def update(row_id: int, values: dict[str, any]) -> dict[str, any]:
        raise NotImplementedError("Product update indexing not implemented")

    @staticmethod
    async def delete(row_id: int) -> None:
        raise NotImplementedError("Product deletion indexing not implemented")
