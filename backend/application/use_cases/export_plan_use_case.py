"""
ExportPlanUseCase — Exportación de planes nutricionales a PDF.

Flujo:
  1. Cargar plan y verificar que existe.
  2. Verificar estado ACTIVE (solo exportable si ACTIVE).
  3. Verificar RBAC (owner o vet asignado).
  4. Calcular content hash SHA-256 para cache.
  5. Cache check: si el PDF ya existe en R2 → devolver URL directamente.
  6. Generar PDF con PDFGenerator.
  7. Subir PDF a R2.
  8. Generar pre-signed URL (TTL 3600s fijo).

Constitution REGLA 8: disclaimer en todas las páginas del PDF.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.application.interfaces.pdf_generator import IPDFGenerator
from backend.application.interfaces.plan_repository import IPlanRepository
from backend.application.interfaces.storage_client import IStorageClient
from backend.domain.aggregates.nutrition_plan import PlanStatus

_PDF_DISCLAIMER = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)
_PRESIGNED_TTL = 3600  # segundos — no configurable (Constitution)
_PDF_KEY_PREFIX = "pdfs"


class ExportNotAllowedError(Exception):
    """Plan no está en estado ACTIVE — no es exportable."""


class ExportForbiddenError(Exception):
    """El usuario no tiene permiso para exportar este plan."""


class PlanNotFoundError(Exception):
    """Plan no encontrado."""


@dataclass(frozen=True)
class ExportResult:
    """Resultado de la exportación: URL pre-signed y timestamp de expiración."""

    url: str
    expires_at: datetime


class ExportPlanUseCase:
    """
    Caso de uso: exportar plan nutricional a PDF.

    Solo planes ACTIVE. RBAC: owner o vet asignado.
    Cache: mismo plan → mismo PDF (no re-genera si ya existe en R2).
    """

    def __init__(
        self,
        plan_repo: IPlanRepository,
        pdf_generator: IPDFGenerator,
        storage_client: IStorageClient,
    ) -> None:
        self._plan_repo = plan_repo
        self._pdf_generator = pdf_generator
        self._storage_client = storage_client

    async def export(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> ExportResult:
        """
        Exporta el plan a PDF y retorna la URL pre-signed.

        Args:
            plan_id: UUID del plan a exportar.
            user_id: UUID del usuario solicitante.

        Returns:
            ExportResult con url y expires_at.

        Raises:
            PlanNotFoundError: Si el plan no existe.
            ExportNotAllowedError: Si el plan no está en ACTIVE.
            ExportForbiddenError: Si el usuario no es owner ni vet asignado.
        """
        # 1. Cargar plan
        plan = await self._plan_repo.find_by_id(plan_id)
        if plan is None:
            raise PlanNotFoundError(f"Plan {plan_id} no encontrado.")

        # 2. Verificar estado
        if plan.status != PlanStatus.ACTIVE:
            raise ExportNotAllowedError(
                f"Solo planes en estado ACTIVE son exportables. "
                f"Estado actual: {plan.status.value}. "
                f"Los planes ACTIVE han sido aprobados y son compartibles."
            )

        # 3. Verificar RBAC
        is_owner = plan.owner_id == user_id
        is_vet = plan.approved_by_vet_id is not None and plan.approved_by_vet_id == user_id
        if not is_owner and not is_vet:
            raise ExportForbiddenError(
                "No tienes permiso para exportar este plan. "
                "Solo el dueño de la mascota o el veterinario asignado pueden exportarlo."
            )

        # 4. Calcular content hash para cache
        plan_data = self._build_plan_data(plan)
        content_hash = self.compute_content_hash(plan_data)
        r2_key = f"{_PDF_KEY_PREFIX}/{plan_id}/{content_hash}.pdf"

        # 5. Cache check
        if self._storage_client.exists(r2_key):
            url = self._storage_client.generate_presigned_url(r2_key, expires_in=_PRESIGNED_TTL)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=_PRESIGNED_TTL)
            return ExportResult(url=url, expires_at=expires_at)

        # 6. Generar PDF
        pdf_bytes = self._pdf_generator.generate(plan_data)

        # 7. Subir a R2
        self._storage_client.upload(r2_key, pdf_bytes, "application/pdf")

        # 8. Generar URL pre-signed
        url = self._storage_client.generate_presigned_url(r2_key, expires_in=_PRESIGNED_TTL)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=_PRESIGNED_TTL)

        return ExportResult(url=url, expires_at=expires_at)

    @staticmethod
    def compute_content_hash(plan_data: dict) -> str:
        """
        Calcula el hash SHA-256 determinístico del contenido del plan.

        Mismo plan → mismo hash → mismo PDF en R2 (cache hit).

        Args:
            plan_data: Diccionario de datos del plan.

        Returns:
            Hash SHA-256 en hexadecimal (64 caracteres).
        """
        import json
        content_str = json.dumps(plan_data, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    @staticmethod
    def _build_plan_data(plan) -> dict:
        """Construye el dict de datos para el PDFGenerator desde el NutritionPlan."""
        content = plan.content or {}
        return {
            "plan_id": str(plan.plan_id),
            "pet_id": str(plan.pet_id),
            "rer_kcal": plan.rer_kcal,
            "der_kcal": plan.der_kcal,
            "modality": plan.modality.value,
            "plan_type": plan.plan_type.value,
            "llm_model_used": plan.llm_model_used,
            "approved_by_vet_name": content.get("approved_by_vet_name"),
            "seccion_1_perfil": content.get("seccion_1_perfil", {}),
            "seccion_2_calorias": content.get("seccion_2_calorias", {
                "rer_kcal": plan.rer_kcal,
                "der_kcal": plan.der_kcal,
                "fase": plan.weight_phase.value,
            }),
            "seccion_3_ingredientes": content.get("seccion_3_ingredientes", []),
            "seccion_4_transicion": content.get("seccion_4_transicion"),
            "seccion_5_sustitutos": content.get("seccion_5_sustitutos", []),
            "has_transition_protocol": content.get("has_transition_protocol", False),
            "disclaimer": _PDF_DISCLAIMER,
        }
