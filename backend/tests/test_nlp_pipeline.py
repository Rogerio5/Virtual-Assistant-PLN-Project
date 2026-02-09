# tests/test_nlp_pipeline.py
import pytest
from typing import cast, Any

from backend.models.nlp_pipeline import NLPPipeline
from backend.models.entity_model import EntityExtractor
from backend.models.intent_model import IntentClassifier


class DummyIntentModel:
    def __init__(self, intent_map=None):
        self.intent_map = intent_map or {}

    def load(self):
        # simula modelo carregado
        return None

    def predict(self, text: str):
        # retorna intent baseado em palavras-chave simples
        for k, v in self.intent_map.items():
            if k in text:
                return v
        return "unknown_intent"


class DummyEntityExtractor:
    def extract_entities(self, text: str):
        # extrai tokens que começam com @ como entidades de exemplo
        return [{"type": "mention", "value": tok[1:]} for tok in text.split() if tok.startswith("@")]


def test_pipeline_basic_flow():
    intent_map = {"abrir": "abrir_app", "tocar": "tocar_audio", "buscar": "buscar_info"}
    intent_model = DummyIntentModel(intent_map=intent_map)
    entity_extractor = DummyEntityExtractor()

    # cast para satisfazer o verificador de tipos (Pylance) sem alterar comportamento em tempo de execução
    pipeline = NLPPipeline(
        entity_extractor=cast(EntityExtractor, entity_extractor),
        intent_classifier=cast(IntentClassifier, intent_model),
        auto_load_intent_model=False,
    )

    out = pipeline.process("Quero abrir o app do calendário")
    assert out["intent"] == "abrir_app"
    assert isinstance(out["entities"], list)
    assert "Abrindo" in out["response"]

    out2 = pipeline.process("Por favor tocar minha playlist")
    assert out2["intent"] == "tocar_audio"
    assert "Tocando" in out2["response"]

    out3 = pipeline.process("Pode buscar informações sobre Python?")
    assert out3["intent"] == "buscar_info"
    assert "Buscando" in out3["response"]


def test_pipeline_entities_extraction():
    intent_model = DummyIntentModel(intent_map={"dummy": "unknown_intent"})
    entity_extractor = DummyEntityExtractor()
    pipeline = NLPPipeline(
        entity_extractor=cast(EntityExtractor, entity_extractor),
        intent_classifier=cast(IntentClassifier, intent_model),
        auto_load_intent_model=False,
    )

    out = pipeline.process("Olá @maria, veja isso")
    assert out["entities"] == [{"type": "mention", "value": "maria"}]


def test_pipeline_handles_invalid_input():
    # cria pipeline real (usa implementações reais por padrão)
    pipeline = NLPPipeline(auto_load_intent_model=False)
    # cast para Any ao chamar process com tipo inválido para evitar aviso do verificador de tipos
    out = cast(Any, pipeline).process(123)  # int intencional para testar validação
    assert out["intent"] is None
    assert out["entities"] == []
    assert "inválida" in out["response"]
