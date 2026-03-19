"""
Tests para PetProfile Aggregate — NutriVet.IA
Fase TDD: RED → GREEN

PetProfile es el aggregate raíz del contexto Pet Management.
Encapsula los 13 campos obligatorios con sus invariantes.
"""
import pytest
from uuid import uuid4


class TestPetProfileCreation:

    def test_crear_pet_profile_perro_valido(self):
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile, ReproductiveStatus,
            Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS
        perfil = PetProfile(
            pet_id=uuid4(),
            owner_id=uuid4(),
            name="Thor",
            species=Species.PERRO,
            breed="Golden Retriever",
            sex=Sex.MACHO,
            age_months=48,
            weight_kg=30.0,
            size=Size.GRANDE,
            reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
            activity_level=DogActivityLevel.ACTIVO,
            bcs=BCS(5),
            medical_conditions=[],
            allergies=[],
            current_diet=CurrentDiet.NATURAL,
        )
        assert perfil.name == "Thor"
        assert perfil.species == Species.PERRO

    def test_crear_pet_profile_gato_valido(self):
        from backend.domain.aggregates.pet_profile import (
            CatActivityLevel, CurrentDiet, PetProfile, ReproductiveStatus,
            Sex, Species,
        )
        from backend.domain.value_objects.bcs import BCS
        perfil = PetProfile(
            pet_id=uuid4(),
            owner_id=uuid4(),
            name="Michi",
            species=Species.GATO,
            breed="Doméstico mixto",
            sex=Sex.HEMBRA,
            age_months=36,
            weight_kg=4.5,
            size=None,
            reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=CatActivityLevel.INDOOR,
            bcs=BCS(5),
            medical_conditions=[],
            allergies=[],
            current_diet=CurrentDiet.CONCENTRADO,
        )
        assert perfil.size is None
        assert perfil.species == Species.GATO

    def test_talla_requerida_para_perro(self):
        """Perro sin talla debe lanzar error."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile, ReproductiveStatus,
            Sex, Species,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(DomainError):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="Rex", species=Species.PERRO, breed="Beagle",
                sex=Sex.MACHO, age_months=24, weight_kg=12.0,
                size=None,  # ← inválido para perro
                reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
                activity_level=DogActivityLevel.MODERADO,
                bcs=BCS(5), medical_conditions=[], allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )

    def test_gato_sin_talla_es_valido(self):
        """Gato con size=None es correcto."""
        from backend.domain.aggregates.pet_profile import (
            CatActivityLevel, CurrentDiet, PetProfile, ReproductiveStatus,
            Sex, Species,
        )
        from backend.domain.value_objects.bcs import BCS
        perfil = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Luna", species=Species.GATO, breed="Siamés",
            sex=Sex.HEMBRA, age_months=24, weight_kg=3.8,
            size=None,
            reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=CatActivityLevel.INDOOR,
            bcs=BCS(5), medical_conditions=[], allergies=[],
            current_diet=CurrentDiet.CONCENTRADO,
        )
        assert perfil.size is None

    def test_gato_con_talla_lanza_error(self):
        """Gato NO debe tener talla — los gatos no tienen clasificación por talla."""
        from backend.domain.aggregates.pet_profile import (
            CatActivityLevel, CurrentDiet, PetProfile, ReproductiveStatus,
            Sex, Size, Species,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(DomainError):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="Felix", species=Species.GATO, breed="Persa",
                sex=Sex.MACHO, age_months=36, weight_kg=5.0,
                size=Size.PEQUEÑO,  # ← inválido para gato
                reproductive_status=ReproductiveStatus.ESTERILIZADO,
                activity_level=CatActivityLevel.INDOOR,
                bcs=BCS(5), medical_conditions=[], allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )

    def test_activity_level_perro_invalido_para_gato(self):
        """Gato con DogActivityLevel debe lanzar error."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile, ReproductiveStatus,
            Sex, Species,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(DomainError):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="Felix", species=Species.GATO, breed="Persa",
                sex=Sex.MACHO, age_months=36, weight_kg=5.0,
                size=None,
                reproductive_status=ReproductiveStatus.ESTERILIZADO,
                activity_level=DogActivityLevel.SEDENTARIO,  # ← inválido para gato
                bcs=BCS(5), medical_conditions=[], allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )

    def test_activity_level_gato_invalido_para_perro(self):
        """Perro con CatActivityLevel debe lanzar error."""
        from backend.domain.aggregates.pet_profile import (
            CatActivityLevel, CurrentDiet, PetProfile, ReproductiveStatus,
            Sex, Size, Species,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(DomainError):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="Rex", species=Species.PERRO, breed="Beagle",
                sex=Sex.MACHO, age_months=24, weight_kg=12.0,
                size=Size.MEDIANO,
                reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
                activity_level=CatActivityLevel.INDOOR,  # ← inválido para perro
                bcs=BCS(5), medical_conditions=[], allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )

    def test_peso_negativo_lanza_error(self):
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile, ReproductiveStatus,
            Sex, Size, Species,
        )
        from backend.domain.exceptions.domain_errors import InvalidWeightError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(InvalidWeightError):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="Rex", species=Species.PERRO, breed="Beagle",
                sex=Sex.MACHO, age_months=24, weight_kg=-5.0,
                size=Size.MEDIANO,
                reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
                activity_level=DogActivityLevel.MODERADO,
                bcs=BCS(5), medical_conditions=[], allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )

    def test_nombre_vacio_lanza_error(self):
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile, ReproductiveStatus,
            Sex, Size, Species,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(DomainError):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="",  # ← inválido
                species=Species.PERRO, breed="Beagle",
                sex=Sex.MACHO, age_months=24, weight_kg=12.0,
                size=Size.MEDIANO,
                reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
                activity_level=DogActivityLevel.MODERADO,
                bcs=BCS(5), medical_conditions=[], allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )

    def test_condicion_medica_desconocida_lanza_error(self):
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, MedicalCondition, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises((DomainError, ValueError)):
            PetProfile(
                pet_id=uuid4(), owner_id=uuid4(),
                name="Rex", species=Species.PERRO, breed="Beagle",
                sex=Sex.MACHO, age_months=24, weight_kg=12.0,
                size=Size.MEDIANO,
                reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
                activity_level=DogActivityLevel.MODERADO,
                bcs=BCS(5),
                medical_conditions=["condicion_inventada"],  # ← debe ser MedicalCondition
                allergies=[],
                current_diet=CurrentDiet.CONCENTRADO,
            )


class TestPetProfileMethods:

    def _make_perro(self, condiciones=None):
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, MedicalCondition, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS
        return PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Thor", species=Species.PERRO, breed="Golden Retriever",
            sex=Sex.MACHO, age_months=48, weight_kg=30.0,
            size=Size.GRANDE,
            reproductive_status=ReproductiveStatus.NO_ESTERILIZADO,
            activity_level=DogActivityLevel.ACTIVO,
            bcs=BCS(5),
            medical_conditions=condiciones or [],
            allergies=[],
            current_diet=CurrentDiet.NATURAL,
        )

    def test_requires_vet_review_true_con_condicion(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        perfil = self._make_perro(condiciones=[MedicalCondition.DIABETICO])
        assert perfil.requires_vet_review() is True

    def test_requires_vet_review_false_sin_condicion(self):
        perfil = self._make_perro(condiciones=[])
        assert perfil.requires_vet_review() is False

    def test_llm_routing_key_sin_condiciones_es_cero(self):
        perfil = self._make_perro(condiciones=[])
        assert perfil.llm_routing_key() == 0

    def test_llm_routing_key_con_condiciones(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        perfil = self._make_perro(condiciones=[
            MedicalCondition.DIABETICO,
            MedicalCondition.RENAL,
            MedicalCondition.GASTRITIS,
        ])
        assert perfil.llm_routing_key() == 3

    def test_condiciones_duplicadas_no_permitidas(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        from backend.domain.exceptions.domain_errors import DomainError
        with pytest.raises(DomainError):
            self._make_perro(condiciones=[
                MedicalCondition.DIABETICO,
                MedicalCondition.DIABETICO,  # duplicado
            ])

    def test_sally_golden_case_profile(self):
        """Caso Sally: 5 condiciones, requires_vet_review=True, llm_routing_key=5."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, MedicalCondition, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS
        sally = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Sally", species=Species.PERRO, breed="French Poodle",
            sex=Sex.HEMBRA, age_months=96, weight_kg=10.08,
            size=Size.PEQUEÑO,
            reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.SEDENTARIO,
            bcs=BCS(6),
            medical_conditions=[
                MedicalCondition.DIABETICO,
                MedicalCondition.HEPATICO_HIPERLIPIDEMIA,
                MedicalCondition.GASTRITIS,
                MedicalCondition.CISTITIS_URINARIA,
                MedicalCondition.HIPOTIROIDEO,
            ],
            allergies=[],
            current_diet=CurrentDiet.CONCENTRADO,
        )
        assert sally.requires_vet_review() is True
        assert sally.llm_routing_key() == 5
        assert sally.bcs.phase.value == "mantenimiento"
