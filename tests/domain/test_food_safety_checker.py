"""
Tests para FoodSafetyChecker — NutriVet.IA
REGLA 1 de la Constitution: tolerancia CERO con ingredientes tóxicos.
El LLM NUNCA decide toxicidad — solo este checker determinista.
"""
import pytest


class TestCheckIngredient:
    """Verificación individual de ingredientes."""

    def test_uvas_toxico_para_perro(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        result = FoodSafetyChecker.check_ingredient("uvas", "perro")
        assert result.is_toxic is True
        assert "perro" in result.affects_species

    def test_uvas_toxico_para_gato(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        result = FoodSafetyChecker.check_ingredient("uvas", "gato")
        assert result.is_toxic is True

    def test_chocolate_toxico_ambas_especies(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("chocolate", "perro").is_toxic is True
        assert FoodSafetyChecker.check_ingredient("chocolate", "gato").is_toxic is True

    def test_lilium_toxico_solo_gato_no_perro(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("lilium", "gato").is_toxic is True
        assert FoodSafetyChecker.check_ingredient("lilium", "perro").is_toxic is False

    def test_aguacate_toxico_para_perro(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("aguacate", "perro").is_toxic is True

    def test_pollo_seguro_ambas_especies(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("pollo", "perro").is_toxic is False
        assert FoodSafetyChecker.check_ingredient("pollo", "gato").is_toxic is False

    def test_ingrediente_case_insensitive(self):
        """La verificación debe ser insensible a mayúsculas."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("CEBOLLA", "perro").is_toxic is True
        assert FoodSafetyChecker.check_ingredient("Ajo", "perro").is_toxic is True
        assert FoodSafetyChecker.check_ingredient("CHOCOLATE", "gato").is_toxic is True

    def test_nombre_cientifico_vitis_vinifera_detectado(self):
        """vitis vinifera = uvas — nombre científico debe detectarse."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        result = FoodSafetyChecker.check_ingredient("vitis vinifera", "perro")
        assert result.is_toxic is True

    def test_nombre_cientifico_allium_sativum_detectado(self):
        """allium sativum = ajo."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        result = FoodSafetyChecker.check_ingredient("allium sativum", "perro")
        assert result.is_toxic is True

    def test_nombre_cientifico_theobroma_cacao_detectado(self):
        """theobroma cacao = cacao/chocolate."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        result = FoodSafetyChecker.check_ingredient("theobroma cacao", "gato")
        assert result.is_toxic is True

    def test_nombre_cientifico_persea_americana_detectado(self):
        """persea americana = aguacate — solo tóxico para perros."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("persea americana", "perro").is_toxic is True

    def test_xilitol_toxico_perro(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("xilitol", "perro").is_toxic is True

    def test_paracetamol_toxico_gato(self):
        """paracetamol/acetaminofén — tóxico crítico para gatos."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        assert FoodSafetyChecker.check_ingredient("paracetamol", "gato").is_toxic is True
        assert FoodSafetyChecker.check_ingredient("acetaminofén", "gato").is_toxic is True


class TestValidatePlanIngredients:
    """Verificación de lista de ingredientes de un plan completo."""

    def test_lista_limpia_retorna_vacio(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        ingredientes = ["pollo", "arroz", "zanahoria", "calabaza", "aceite de salmón"]
        resultados = FoodSafetyChecker.validate_plan_ingredients(ingredientes, "perro")
        toxicos = [r for r in resultados if r.is_toxic]
        assert len(toxicos) == 0

    def test_lista_mixta_retorna_todos_los_toxicos(self):
        """Una lista con varios tóxicos debe reportar todos."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        ingredientes = ["pollo", "uvas", "arroz", "cebolla", "zanahoria"]
        resultados = FoodSafetyChecker.validate_plan_ingredients(ingredientes, "perro")
        toxicos = [r for r in resultados if r.is_toxic]
        nombres_toxicos = {r.ingredient for r in toxicos}
        assert "uvas" in nombres_toxicos
        assert "cebolla" in nombres_toxicos
        assert len(toxicos) == 2

    def test_lista_vacia_retorna_vacio(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        resultados = FoodSafetyChecker.validate_plan_ingredients([], "perro")
        assert len(resultados) == 0

    def test_especie_invalida_lanza_error(self):
        from backend.domain.exceptions.domain_errors import NRCCalculationError
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        with pytest.raises((ValueError, NRCCalculationError)):
            FoodSafetyChecker.validate_plan_ingredients(["pollo"], "iguana")


class TestGetToxicListForSpecies:
    """Acceso a las listas de tóxicos por especie."""

    def test_lista_perro_contiene_minimos_requeridos(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        lista = FoodSafetyChecker.get_toxic_list_for_species("perro")
        # Ingredientes mínimos obligatorios según Constitution REGLA 1
        for toxico in ["uvas", "cebolla", "ajo", "xilitol", "chocolate", "macadamia"]:
            assert toxico in lista, f"'{toxico}' debe estar en TOXIC_DOGS"

    def test_lista_gato_contiene_minimos_requeridos(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        lista = FoodSafetyChecker.get_toxic_list_for_species("gato")
        for toxico in ["cebolla", "ajo", "uvas", "chocolate", "cafeína", "xilitol"]:
            assert toxico in lista, f"'{toxico}' debe estar en TOXIC_CATS"

    def test_lista_es_inmutable(self):
        """Las listas de tóxicos no deben ser modificables externamente."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        lista = FoodSafetyChecker.get_toxic_list_for_species("perro")
        # frozenset no tiene add/remove — cualquier intento de mutación falla
        assert not hasattr(lista, "add"), "La lista de tóxicos debe ser un frozenset"
