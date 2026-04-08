"""
Modelos ORM SQLAlchemy — tablas users, refresh_tokens, pets, weight_records, claim_codes.
Estos modelos son solo para persistencia; las entidades de dominio viven en domain/.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import BYTEA, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.infrastructure.db.base import Base


class UserModel(Base):
    """Tabla users — almacena cuentas de usuario del sistema."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("owner", "vet", "admin", name="user_role_enum"), nullable=False
    )
    tier: Mapped[str] = mapped_column(
        Enum("free", "basico", "premium", "vet", name="user_tier_enum"),
        nullable=False,
        default="free",
    )
    subscription_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True, default=None)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, default=None)
    clinic_name: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    specialization: Mapped[str | None] = mapped_column(String(150), nullable=True, default=None)
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    vet_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )  # pending | approved | rejected — solo para rol vet
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relación con refresh tokens
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshTokenModel(Base):
    """Tabla refresh_tokens — almacena tokens de refresco rotativos."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relación con usuario
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="refresh_tokens")


class PetModel(Base):
    """Tabla pets — perfiles de mascotas (AppPet y ClinicPet)."""

    __tablename__ = "pets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    vet_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, default=None, index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str] = mapped_column(
        Enum("perro", "gato", name="species_enum"), nullable=False
    )
    breed: Mapped[str] = mapped_column(String(100), nullable=False)
    sex: Mapped[str] = mapped_column(
        Enum("macho", "hembra", name="sex_enum"), nullable=False
    )
    age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(nullable=False)
    size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reproductive_status: Mapped[str] = mapped_column(String(30), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(30), nullable=False)
    bcs: Mapped[int] = mapped_column(Integer, nullable=False)
    # Campos médicos encriptados AES-256 (Fernet) en reposo — Constitution REGLA 6
    medical_conditions_enc: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)
    allergies_enc: Mapped[bytes | None] = mapped_column(BYTEA, nullable=True)
    current_diet: Mapped[str] = mapped_column(String(20), nullable=False, default="concentrado")
    is_clinic_pet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Datos del dueño (solo para ClinicPet, antes del claim)
    owner_name_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner_phone_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    weight_records: Mapped[list["WeightRecordModel"]] = relationship(
        "WeightRecordModel", back_populates="pet", cascade="all, delete-orphan"
    )
    claim_codes: Mapped[list["ClaimCodeModel"]] = relationship(
        "ClaimCodeModel", back_populates="pet", cascade="all, delete-orphan"
    )


class WeightRecordModel(Base):
    """Tabla weight_records — historial de peso append-only."""

    __tablename__ = "weight_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    weight_kg: Mapped[float] = mapped_column(nullable=False)
    bcs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pet: Mapped["PetModel"] = relationship("PetModel", back_populates="weight_records")


class ClaimCodeModel(Base):
    """Tabla claim_codes — códigos de reclamación para ClinicPet (single-use, TTL 30 días)."""

    __tablename__ = "claim_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    pet: Mapped["PetModel"] = relationship("PetModel", back_populates="claim_codes")


class NutritionPlanModel(Base):
    """Tabla nutrition_plans — planes nutricionales generados por el agente."""

    __tablename__ = "nutrition_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    plan_type: Mapped[str] = mapped_column(
        Enum("estándar", "temporal_medical", "life_stage", name="plan_type_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("PENDING_VET", "ACTIVE", "UNDER_REVIEW", "ARCHIVED", name="plan_status_enum"),
        nullable=False, index=True,
    )
    modality: Mapped[str] = mapped_column(
        Enum("natural", "concentrado", name="plan_modality_enum"), nullable=False
    )
    rer_kcal: Mapped[float] = mapped_column(Float, nullable=False)
    der_kcal: Mapped[float] = mapped_column(Float, nullable=False)
    weight_phase: Mapped[str] = mapped_column(String(20), nullable=False)
    llm_model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # HITL
    approved_by_vet_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    approval_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    vet_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Trazabilidad
    agent_trace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PlanJobModel(Base):
    """Tabla plan_jobs — jobs asíncronos de generación de planes (ARQ)."""

    __tablename__ = "plan_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    modality: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("QUEUED", "PROCESSING", "READY", "FAILED", name="job_status_enum"),
        nullable=False, default="QUEUED",
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_message: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SubstituteSetModel(Base):
    """Tabla substitute_sets — ingredientes aprobados para sustitución sin HITL."""

    __tablename__ = "substitute_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nutrition_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    ingredient: Mapped[str] = mapped_column(String(100), nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AgentTraceModel(Base):
    """
    Tabla agent_traces — trazas de ejecución del agente LLM (append-only).

    REGLA 6: Sin updated_at — inmutables post-inserción.
    Solo INSERT permitido — nunca UPDATE.
    """

    __tablename__ = "agent_traces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # NOTA: No existe updated_at — trazas son inmutables (Constitution REGLA 6)


class LabelScanModel(Base):
    """
    Tabla label_scans — registro de escaneos de etiquetas nutricionales.

    SIN columna brand_name — principio de imparcialidad (Constitution REGLA 7).
    """

    __tablename__ = "label_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # nutrition_table | ingredient_list
    semaphore: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # ROJO | AMARILLO | VERDE
    ingredients_detected: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=list
    )  # lista de ingredientes extraídos
    issues: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=list
    )  # problemas detectados
    recomendacion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # brand_name EXCLUIDO intencionalmente — principio de imparcialidad (REGLA 7)


class ConversationModel(Base):
    """
    Tabla conversations — historial de conversaciones nutricionales.

    Almacena mensajes del usuario y respuestas del agente para contexto conversacional.
    SIN datos PII — solo IDs anónimos (Constitution REGLA 6).
    """

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # nutritional | medical | emergency
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Sin updated_at — historial es append-only (REGLA 6)


class DeviceTokenModel(Base):
    """
    Tabla device_tokens — tokens FCM para push notifications.

    Cada usuario puede tener múltiples tokens (dispositivos).
    El token se registra al hacer login y se elimina al logout.
    """

    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    token: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    platform: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "android" | "ios"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )


class PaymentModel(Base):
    """
    Tabla payments — registro de pagos vía PayU Colombia.

    Cada pago corresponde a la activación/renovación de un tier de suscripción.
    Estado: pending → approved | declined | error.
    Los pagos son append-only — nunca se modifica un registro existente.
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    reference_code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    tier: Mapped[str] = mapped_column(String(20), nullable=False)  # basico | premium | vet
    amount_cop: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False, default="COP")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | approved | declined | error
    payu_transaction_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    payu_order_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    raw_webhook: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )


class AgentQuotaModel(Base):
    """
    Tabla agent_quotas — cuota de uso del agente conversacional para tier Free.

    Free tier: 3 preguntas/día × 3 días = 9 total.
    """

    __tablename__ = "agent_quotas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    daily_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reset_date: Mapped[str] = mapped_column(
        String(10), nullable=False, default=""
    )  # formato ISO: YYYY-MM-DD
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
