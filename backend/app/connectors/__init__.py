"""Public data connector subsystem.

Provides an extensible abstraction for retrieving, validating, normalizing,
recording provenance, and storing external civic datasets from public portals.
"""

from __future__ import annotations

from app.connectors.base import BasePublicDataConnector
from app.connectors.civic_open_data import CivicOpenDataConnector
from app.connectors.exceptions import (
    ConnectorError,
    ConnectorFetchError,
    ConnectorNormalizationError,
    ConnectorValidationError,
)
from app.connectors.models import (
    ConnectorFetchResult,
    ConnectorProvenance,
    NormalizedDataset,
)
from app.connectors.registry import (
    ConnectorRegistry,
    connector_registry,
    get_connector_registry,
)

# Register default first-party civic open data connector
default_civic_connector = CivicOpenDataConnector()
connector_registry.register("civic_open_data", default_civic_connector)
connector_registry.register("generic_http", default_civic_connector)

__all__ = [
    "BasePublicDataConnector",
    "CivicOpenDataConnector",
    "ConnectorProvenance",
    "ConnectorFetchResult",
    "NormalizedDataset",
    "ConnectorRegistry",
    "connector_registry",
    "get_connector_registry",
    "ConnectorError",
    "ConnectorFetchError",
    "ConnectorValidationError",
    "ConnectorNormalizationError",
]
