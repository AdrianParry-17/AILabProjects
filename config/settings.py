"""Application-level settings (single source of truth)."""

from __future__ import annotations

PROJECT_NAME = "HCMC Delivery AI Search Lab"
PROJECT_VERSION = "1.0.0"

# Shared JSON dataset schema version. Consumed by `data.models`, `delivery.models`
# and both loaders via `config`; bump (with the JSON files and docs) on any breaking
# change to Node/Edge/DeliveryNode/DeliveryEdge.
SCHEMA_VERSION = "1.0"
