"""
Tests para Value Objects del domain layer — NutriVet.IA
Fase TDD: RED (deben FALLAR hasta implementar los value objects)
"""
import pytest


class TestBCS:
    """BCS — Body Condition Score (1-9)."""

    def test_bcs_valido_entre_1_y_9(self):
        from backend.domain.value_objects.bcs import BCS
        for valor in range(1, 10):
            bcs = BCS(valor)
            assert bcs.value == valor

    def test_bcs_invalido_cero_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidBCSError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(InvalidBCSError):
            BCS(0)

    def test_bcs_invalido_diez_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidBCSError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(InvalidBCSError):
            BCS(10)

    def test_bcs_invalido_negativo_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidBCSError
        from backend.domain.value_objects.bcs import BCS
        with pytest.raises(InvalidBCSError):
            BCS(-1)

    def test_bcs_phase_reduccion_si_bcs_mayor_igual_7(self):
        from backend.domain.value_objects.bcs import BCS, BCSPhase
        assert BCS(7).phase == BCSPhase.REDUCCION
        assert BCS(8).phase == BCSPhase.REDUCCION
        assert BCS(9).phase == BCSPhase.REDUCCION

    def test_bcs_phase_mantenimiento_entre_4_y_6(self):
        from backend.domain.value_objects.bcs import BCS, BCSPhase
        assert BCS(4).phase == BCSPhase.MANTENIMIENTO
        assert BCS(5).phase == BCSPhase.MANTENIMIENTO
        assert BCS(6).phase == BCSPhase.MANTENIMIENTO

    def test_bcs_phase_aumento_si_bcs_menor_igual_3(self):
        from backend.domain.value_objects.bcs import BCS, BCSPhase
        assert BCS(1).phase == BCSPhase.AUMENTO
        assert BCS(2).phase == BCSPhase.AUMENTO
        assert BCS(3).phase == BCSPhase.AUMENTO

    def test_bcs_der_factor_reduccion_es_0_8(self):
        from backend.domain.value_objects.bcs import BCS
        # BCS 7+ → factor de reducción 0.8 (aplicado sobre RER de peso ideal)
        assert BCS(7).der_modifier == 0.8

    def test_bcs_der_factor_mantenimiento_es_1(self):
        from backend.domain.value_objects.bcs import BCS
        assert BCS(5).der_modifier == 1.0

    def test_bcs_der_factor_aumento_es_1_2(self):
        from backend.domain.value_objects.bcs import BCS
        assert BCS(2).der_modifier == 1.2

    def test_bcs_es_inmutable(self):
        from backend.domain.value_objects.bcs import BCS
        bcs = BCS(5)
        with pytest.raises((AttributeError, TypeError)):
            bcs.value = 7  # type: ignore


class TestEmailAddress:
    """EmailAddress — value object para email válido."""

    def test_email_valido(self):
        from backend.domain.value_objects.email_address import EmailAddress
        email = EmailAddress("sadid@nutrivet.ai")
        assert email.value == "sadid@nutrivet.ai"

    def test_email_invalido_sin_arroba_lanza_error(self):
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.email_address import EmailAddress
        with pytest.raises(DomainError):
            EmailAddress("nodomain.com")

    def test_email_invalido_sin_punto_lanza_error(self):
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.email_address import EmailAddress
        with pytest.raises(DomainError):
            EmailAddress("user@nodot")

    def test_email_vacio_lanza_error(self):
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.email_address import EmailAddress
        with pytest.raises(DomainError):
            EmailAddress("")

    def test_email_normalizado_a_lowercase(self):
        from backend.domain.value_objects.email_address import EmailAddress
        email = EmailAddress("Sadid@NutriVet.AI")
        assert email.value == "sadid@nutrivet.ai"

    def test_email_es_inmutable(self):
        from backend.domain.value_objects.email_address import EmailAddress
        email = EmailAddress("sadid@nutrivet.ai")
        with pytest.raises((AttributeError, TypeError)):
            email.value = "otro@email.com"  # type: ignore


class TestPositiveDecimal:
    """PositiveDecimal — value object para peso y medidas positivas."""

    def test_peso_valido_positivo(self):
        from backend.domain.value_objects.positive_decimal import PositiveDecimal
        pd = PositiveDecimal(9.6)
        assert pd.value == 9.6

    def test_peso_cero_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidWeightError
        from backend.domain.value_objects.positive_decimal import PositiveDecimal
        with pytest.raises(InvalidWeightError):
            PositiveDecimal(0.0)

    def test_peso_negativo_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidWeightError
        from backend.domain.value_objects.positive_decimal import PositiveDecimal
        with pytest.raises(InvalidWeightError):
            PositiveDecimal(-5.0)

    def test_peso_muy_pequeño_valido(self):
        from backend.domain.value_objects.positive_decimal import PositiveDecimal
        # Chihuahua pequeño ~1kg es válido
        pd = PositiveDecimal(1.0)
        assert pd.value == 1.0

    def test_positive_decimal_es_inmutable(self):
        from backend.domain.value_objects.positive_decimal import PositiveDecimal
        pd = PositiveDecimal(9.6)
        with pytest.raises((AttributeError, TypeError)):
            pd.value = 10.0  # type: ignore
