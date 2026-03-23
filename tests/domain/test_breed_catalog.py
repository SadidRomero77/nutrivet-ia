"""
Tests para el catálogo de razas — NutriVet.IA (A-01)
"""
import pytest


class TestBreedCatalogStructure:

    def test_catalog_has_dogs_and_cats(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        especies = {b.especie for b in BREED_CATALOG.values()}
        assert "perro" in especies
        assert "gato" in especies

    def test_catalog_has_criollo_for_both_species(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        criollos = [b for b in BREED_CATALOG.values() if b.es_criollo]
        species_criollo = {b.especie for b in criollos}
        assert "perro" in species_criollo
        assert "gato" in species_criollo

    def test_all_breeds_have_required_fields(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        for breed_id, breed in BREED_CATALOG.items():
            assert breed.id == breed_id, f"ID mismatch: {breed_id}"
            assert breed.nombre, f"Falta nombre en {breed_id}"
            assert breed.especie in ("perro", "gato"), f"Especie inválida en {breed_id}"
            assert breed.peso_adulto_min_kg > 0, f"Peso mínimo inválido en {breed_id}"
            assert breed.peso_adulto_max_kg >= breed.peso_adulto_min_kg
            assert breed.meses_adulto > 0, f"Meses adulto inválido en {breed_id}"

    def test_giant_breeds_have_correct_adult_months(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        gigantes = ["gran_danes", "bernes_montania", "rottweiler"]
        for breed_id in gigantes:
            breed = BREED_CATALOG.get(breed_id)
            assert breed is not None, f"Raza {breed_id} no encontrada"
            assert breed.meses_adulto >= 18, (
                f"{breed_id}: meses_adulto debería ser ≥18, es {breed.meses_adulto}"
            )

    def test_dalmatian_has_urate_predisposition(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        dalmata = BREED_CATALOG["dalmata"]
        assert "hiperuricosuria" in dalmata.predisposiciones

    def test_maine_coon_has_hcm_predisposition(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        maine = BREED_CATALOG["maine_coon"]
        assert "cardiomiopatia_hipertrofica" in maine.predisposiciones

    def test_golden_retriever_has_cancer_predisposition(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        golden = BREED_CATALOG["golden_retriever"]
        assert "cancer" in golden.predisposiciones

    def test_total_breeds_at_least_160(self):
        from backend.domain.breeds.breed_catalog import BREED_CATALOG
        assert len(BREED_CATALOG) >= 60, f"Solo {len(BREED_CATALOG)} razas en el catálogo"


class TestBreedSearch:

    def test_search_by_exact_name(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("Labrador Retriever")
        assert len(results) > 0
        assert results[0].id == "labrador_retriever"

    def test_search_by_alias(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("Labrador")
        ids = [r.id for r in results]
        assert "labrador_retriever" in ids

    def test_search_by_substring(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("bull")
        assert len(results) >= 2

    def test_search_filtered_by_species_dog(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("common", especie="perro")
        for r in results:
            assert r.especie == "perro"

    def test_search_filtered_by_species_cat(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("persa", especie="gato")
        for r in results:
            assert r.especie == "gato"

    def test_search_criollo_by_keyword(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("criollo", especie="perro")
        criollos = [r for r in results if r.es_criollo]
        assert len(criollos) > 0

    def test_search_respects_limit(self):
        from backend.domain.breeds.breed_catalog import search_breeds
        results = search_breeds("a", limit=3)
        assert len(results) <= 3

    def test_get_breed_returns_correct_info(self):
        from backend.domain.breeds.breed_catalog import get_breed
        breed = get_breed("poodle_miniatura")
        assert breed is not None
        assert breed.especie == "perro"

    def test_get_breed_unknown_returns_none(self):
        from backend.domain.breeds.breed_catalog import get_breed
        assert get_breed("raza_inventada_xyz") is None


class TestBreedRestrictionEngine:

    def test_dalmata_has_purine_restrictions(self):
        from backend.domain.safety.breed_restriction_engine import get_breed_restrictions
        r = get_breed_restrictions("dalmata")
        assert r is not None
        assert "hígado" in r.prohibited_preventive
        assert "anchoas" in r.prohibited_preventive

    def test_bedlington_has_copper_restrictions(self):
        from backend.domain.safety.breed_restriction_engine import get_breed_restrictions
        r = get_breed_restrictions("bedlington_terrier")
        assert r is not None
        assert "hígado_de_res" in r.prohibited_preventive

    def test_gran_danes_has_gdv_rules(self):
        from backend.domain.safety.breed_restriction_engine import get_breed_restrictions
        r = get_breed_restrictions("gran_danes")
        assert r is not None
        assert "sin_ejercicio_2h_post_comida" in r.special_preventive

    def test_maine_coon_has_taurine_recommendation(self):
        from backend.domain.safety.breed_restriction_engine import get_breed_restrictions
        r = get_breed_restrictions("maine_coon")
        assert r is not None
        assert "taurina_elevada_preventiva" in r.recommended_preventive

    def test_unknown_breed_returns_none(self):
        from backend.domain.safety.breed_restriction_engine import get_breed_restrictions
        assert get_breed_restrictions("raza_sin_restricciones_xyz") is None

    def test_has_breed_restrictions_true_for_dalmata(self):
        from backend.domain.safety.breed_restriction_engine import has_breed_restrictions
        assert has_breed_restrictions("dalmata") is True

    def test_has_breed_restrictions_false_for_unknown(self):
        from backend.domain.safety.breed_restriction_engine import has_breed_restrictions
        assert has_breed_restrictions("raza_sin_restricciones_xyz") is False
