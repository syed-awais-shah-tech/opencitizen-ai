"""Service layer for civic tabular datasets and DuckDB table management."""

from app.schemas.datasets import DatasetItem, DatasetListResponse


class DatasetsService:
    """Service handling dataset registration, retrieval, and schema inspection."""

    def __init__(self) -> None:
        # In-memory storage for Stage 3; will be backed by DuckDB/PostgreSQL in later stages.
        self._datasets: list[DatasetItem] = []

    def get_datasets(self, limit: int = 50, offset: int = 0) -> DatasetListResponse:
        """Retrieve collection of registered datasets.

        In Stage 3, this returns the initial (empty or registered) collection
        without PostgreSQL persistence.
        """
        paginated = self._datasets[offset : offset + limit]
        return DatasetListResponse(
            items=paginated,
            total=len(self._datasets),
        )


datasets_service = DatasetsService()
