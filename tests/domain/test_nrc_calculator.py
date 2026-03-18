"""
Tests para NRCCalculator — NutriVet.IA
Fase TDD: RED → GREEN

BLOQUEANTE: test_golden_case_sally_rer y test_golden_case_sally_der
deben pasar con ±0.5 kcal de tolerancia (Quality Gate G8).
"""
import pytest


class TestCalculateRER:
    """RER = 70 × peso_kg^0.75"""

    def test_golden_case_sally_rer(self):
        """BLOQUEANTE G8 — RER Sally (10.08 kg) debe ser 396 kcal ±0.5."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(10.08)
        assert abs(rer - 396.0) <= 0.5, f"RER Sally incorrecto: {rer} (esperado 396.0 ±0.5)"

    def test_rer_perro_30kg(self):
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        # RER = 70 × 30^0.75 = 70 × 12.828... ≈ 898.0
        rer = NRCCalculator.calculate_rer(30.0)
        assert 895 <= rer <= 901

    def test_rer_gato_4kg(self):
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        # RER = 70 × 4^0.75 = 70 × 2.828... ≈ 198.0
        rer = NRCCalculator.calculate_rer(4.0)
        assert 196 <= rer <= 200

    def test_rer_peso_cero_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidWeightError
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        with pytest.raises(InvalidWeightError):
            NRCCalculator.calculate_rer(0.0)

    def test_rer_peso_negativo_lanza_error(self):
        from backend.domain.exceptions.domain_errors import InvalidWeightError
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        with pytest.raises(InvalidWeightError):
            NRCCalculator.calculate_rer(-3.5)


class TestCalculateDER:
    """DER = RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs"""

    def test_golden_case_sally_der(self):
        """
        BLOQUEANTE G8 — DER Sally debe ser 534 kcal/día ±0.5.
        Sally: RER=396, 8 años, esterilizada, sedentaria, BCS 6 (mantenimiento).
        """
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(10.08)
        der = NRCCalculator.calculate_der(
            rer=rer,
            age_months=96,
            reproductive_status="esterilizado",
            activity_level="sedentario",
            species="perro",
            bcs=6,
        )
        assert abs(der - 534.0) <= 0.5, f"DER Sally incorrecto: {der} (esperado 534.0 ±0.5)"

    def test_der_factor_bcs_reduccion_aplica_0_8(self):
        """BCS 7+ → DER con modifier 0.8 resulta menor que BCS 5."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = 500.0
        der_mantenimiento = NRCCalculator.calculate_der(
            rer=rer,
            age_months=48,
            reproductive_status="no_esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=5,
        )
        der_reduccion = NRCCalculator.calculate_der(
            rer=rer,
            age_months=48,
            reproductive_status="no_esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=7,
        )
        assert der_reduccion < der_mantenimiento

    def test_der_factor_bcs_aumento_aplica_1_2(self):
        """BCS ≤3 → DER mayor que BCS 5."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = 500.0
        der_mantenimiento = NRCCalculator.calculate_der(
            rer=rer,
            age_months=48,
            reproductive_status="no_esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=5,
        )
        der_aumento = NRCCalculator.calculate_der(
            rer=rer,
            age_months=48,
            reproductive_status="no_esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=2,
        )
        assert der_aumento > der_mantenimiento

    def test_der_cachorro_menor_4_meses_factor_mayor(self):
        """Cachorros < 4 meses tienen DER mayor que adultos."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = 300.0
        der_cachorro = NRCCalculator.calculate_der(
            rer=rer,
            age_months=2,
            reproductive_status="no_esterilizado",
            activity_level="activo",
            species="perro",
            bcs=5,
        )
        der_adulto = NRCCalculator.calculate_der(
            rer=rer,
            age_months=36,
            reproductive_status="no_esterilizado",
            activity_level="activo",
            species="perro",
            bcs=5,
        )
        assert der_cachorro > der_adulto

    def test_der_factor_reproductivo_esterilizado_menor(self):
        """Mascotas esterilizadas tienen DER menor que enteras."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = 400.0
        der_esterilizado = NRCCalculator.calculate_der(
            rer=rer,
            age_months=36,
            reproductive_status="esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=5,
        )
        der_entero = NRCCalculator.calculate_der(
            rer=rer,
            age_months=36,
            reproductive_status="no_esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=5,
        )
        assert der_esterilizado < der_entero

    def test_der_gato_indoor(self):
        """Gato indoor tiene DER calculable sin error."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(4.5)
        der = NRCCalculator.calculate_der(
            rer=rer,
            age_months=36,
            reproductive_status="esterilizado",
            activity_level="indoor",
            species="gato",
            bcs=5,
        )
        assert der > 0

    def test_der_gato_outdoor(self):
        """Gato outdoor tiene DER mayor que indoor."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(4.5)
        der_indoor = NRCCalculator.calculate_der(
            rer=rer,
            age_months=36,
            reproductive_status="no_esterilizado",
            activity_level="indoor",
            species="gato",
            bcs=5,
        )
        der_outdoor = NRCCalculator.calculate_der(
            rer=rer,
            age_months=36,
            reproductive_status="no_esterilizado",
            activity_level="outdoor",
            species="gato",
            bcs=5,
        )
        assert der_outdoor > der_indoor


class TestGetIdealWeightEstimate:
    """Estimación de peso ideal para BCS > 6 (usado en cálculo de reducción)."""

    def test_peso_ideal_bcs_5_igual_al_real(self):
        """BCS 5 = peso ideal, no hay ajuste."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        peso_ideal = NRCCalculator.get_ideal_weight_estimate(10.0, bcs=5)
        assert abs(peso_ideal - 10.0) <= 0.1

    def test_peso_ideal_bcs_7_menor_que_real(self):
        """BCS 7 → peso ideal estimado debe ser menor al peso real."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        peso_ideal = NRCCalculator.get_ideal_weight_estimate(15.0, bcs=7)
        assert peso_ideal < 15.0

    def test_peso_ideal_bcs_9_menor_que_bcs_7(self):
        """BCS 9 (obesidad severa) → ajuste mayor hacia abajo que BCS 7."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        peso_real = 20.0
        peso_ideal_bcs7 = NRCCalculator.get_ideal_weight_estimate(peso_real, bcs=7)
        peso_ideal_bcs9 = NRCCalculator.get_ideal_weight_estimate(peso_real, bcs=9)
        assert peso_ideal_bcs9 < peso_ideal_bcs7

    def test_peso_ideal_positivo_siempre(self):
        """El peso ideal nunca debe ser cero o negativo."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        for bcs in range(1, 10):
            peso_ideal = NRCCalculator.get_ideal_weight_estimate(5.0, bcs=bcs)
            assert peso_ideal > 0
