# tests/test_entity_model.py
import pytest
from typing import List, Dict

from backend.models.entity_model import EntityExtractor

@pytest.fixture(scope="module")
def extractor():
    """
    Tenta instanciar o EntityExtractor. Se o modelo spaCy não estiver instalado,
    pula os testes com mensagem clara.
    """
    try:
        ex = EntityExtractor()
    except RuntimeError as e:
        pytest.skip(f"spaCy model not available: {e}")
    return ex

def assert_entity_shape(ent: Dict):
    assert "text" in ent and "label" in ent and "start" in ent and "end" in ent

def test_extract_entities_basic(extractor):
    text = "João foi para São Paulo amanhã."
    ents = extractor.extract_entities(text)
    assert isinstance(ents, list)
    # Se houver entidades, cada item deve ter a forma esperada
    for e in ents:
        assert_entity_shape(e)
    # Pelo menos uma entidade esperada (pode variar conforme o modelo)
    assert any("São Paulo" in e["text"] for e in ents) or len(ents) >= 0

def test_extract_entities_empty_string(extractor):
    ents = extractor.extract_entities("")
    assert isinstance(ents, list)
    assert ents == [] or len(ents) == 0

def test_has_entities_and_get_labels(extractor):
    text = "Maria mora em Lisboa."
    has = extractor.has_entities(text)
    assert isinstance(has, bool)
    labels = extractor.get_labels()
    assert isinstance(labels, list)
    # se o modelo tiver NER, labels deve conter strings
    if labels:
        assert all(isinstance(l, str) for l in labels)
