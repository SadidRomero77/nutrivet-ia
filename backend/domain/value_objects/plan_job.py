"""
PlanJob — Value object que representa el estado de un job de generación de plan.

Estados: QUEUED → PROCESSING → READY | FAILED
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class PlanJobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


@dataclass
class PlanJob:
    """Representa el estado de un job asíncrono de generación de plan nutricional."""

    job_id: uuid.UUID
    pet_id: uuid.UUID
    owner_id: uuid.UUID
    modality: str
    status: PlanJobStatus = PlanJobStatus.QUEUED
    plan_id: Optional[uuid.UUID] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_processing(self) -> None:
        """Transición QUEUED → PROCESSING."""
        self.status = PlanJobStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_ready(self, plan_id: uuid.UUID) -> None:
        """Transición PROCESSING → READY con plan_id generado."""
        self.status = PlanJobStatus.READY
        self.plan_id = plan_id
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Transición PROCESSING → FAILED con mensaje de error."""
        self.status = PlanJobStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
