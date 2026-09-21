"""Registry for external public-data connectors.

Enables registering and discovering connector implementations dynamically
so future integrations (CKAN, Socrata, Census, OpenDataSoft) can be added
without modifying core ingestion logic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.connectors.exceptions import ConnectorError
from app.schemas.datasets import ConnectorInfo

if TYPE_CHECKING:
    from app.connectors.base import BasePublicDataConnector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Central registry for available public data connectors."""

    def __init__(self) -> None:
        self._connectors: dict[str, BasePublicDataConnector] = {}

    def register(self, connector_id: str, connector: BasePublicDataConnector) -> None:
        """Register a connector implementation under a unique identifier."""
        clean_id = connector_id.strip().lower()
        self._connectors[clean_id] = connector
        logger.info("Registered public data connector '%s' (%s)", clean_id, connector.connector_name)

    def get(self, connector_id: str) -> BasePublicDataConnector:
        """Retrieve a registered connector by identifier."""
        clean_id = connector_id.strip().lower()
        if clean_id not in self._connectors:
            available = ", ".join(sorted(self._connectors.keys()))
            raise ConnectorError(
                f"Connector '{clean_id}' is not registered. Available connectors: [{available}]",
                error_code="CONNECTOR_NOT_FOUND",
            )
        return self._connectors[clean_id]

    def list_connectors(self) -> list[ConnectorInfo]:
        """List metadata for all active registered connectors."""
        return [
            ConnectorInfo(
                id=cid,
                name=conn.connector_name,
                description=conn.description,
                supported_formats=conn.supported_formats,
                enabled=True,
            )
            for cid, conn in sorted(self._connectors.items())
        ]


# Singleton connector registry
connector_registry = ConnectorRegistry()


def get_connector_registry() -> ConnectorRegistry:
    """Dependency provider returning singleton connector registry."""
    return connector_registry
