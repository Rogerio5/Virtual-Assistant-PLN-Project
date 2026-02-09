# backend/models/nlp_pipeline.py
from typing import Any, Dict, Optional
import logging

from backend.models.entity_model import EntityExtractor
from backend.models.intent_model import IntentClassifier

logger = logging.getLogger("nlp_pipeline")


class NLPPipeline:
    """
    Pipeline simples que combina extração de entidades e classificação de intenção.
    Permite injeção de dependências para facilitar testes.
    """

    def __init__(
        self,
        entity_extractor: Optional[EntityExtractor] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        auto_load_intent_model: bool = True,
    ) -> None:
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.intent_classifier = intent_classifier or IntentClassifier()

        if auto_load_intent_model:
            try:
                # load pode lançar se o modelo não estiver treinado; logar em vez de print
                self.intent_classifier.load()
            except Exception:
                logger.warning("Modelo de intenção não treinado ou falha ao carregar. Treine antes de usar.", exc_info=False)

    def process(self, text: str) -> Dict[str, Any]:
        """
        Processa o texto e retorna um dicionário com intent, entities e response.
        Nunca lança exceções por falha de modelo; em caso de erro, retorna valores seguros.
        """
        if not isinstance(text, str):
            logger.error("Entrada inválida para process: esperado str, recebido %s", type(text))
            return {"intent": None, "entities": [], "response": "Entrada inválida."}

        try:
            intent = self.intent_classifier.predict(text)
        except Exception:
            logger.exception("Falha ao predizer intenção; retornando None.")
            intent = None

        try:
            entities = self.entity_extractor.extract_entities(text)
        except Exception:
            logger.exception("Falha ao extrair entidades; retornando lista vazia.")
            entities = []

        response = self.generate_response(intent, entities)
        return {"intent": intent, "entities": entities, "response": response}

    def generate_response(self, intent: Optional[str], entities: Any) -> str:
        """
        Gera uma resposta simples baseada na intenção detectada.
        Pode ser substituída ou estendida para respostas mais sofisticadas.
        """
        mapping = {
            "abrir_app": "Abrindo o aplicativo solicitado...",
            "tocar_audio": "Tocando sua música favorita!",
            "buscar_info": "Buscando informações relevantes...",
        }

        if intent is None:
            return "Desculpe, não entendi sua solicitação."
        return mapping.get(intent, "Desculpe, não entendi sua solicitação.")
