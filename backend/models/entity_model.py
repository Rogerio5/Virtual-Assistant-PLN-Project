# backend/models/entity_model.py
import logging
from typing import List, Dict, Optional

import spacy
from spacy.language import Language
from spacy.util import get_package_path

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extrai entidades nomeadas de um texto usando um modelo spaCy.
    - Por padrão usa "pt_core_news_sm".
    - Se o modelo não estiver instalado, lança RuntimeError com instruções.
    """

    def __init__(self, model_name: str = "pt_core_news_sm"):
        self.model_name = model_name
        self.nlp: Optional[Language] = None
        self._load_model()

    def _load_model(self) -> None:
        """Tenta carregar o modelo spaCy; em caso de falha, informa como instalar."""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info("Modelo spaCy carregado: %s", self.model_name)
        except OSError as exc:
            # Modelo não encontrado — instruções claras para o usuário
            msg = (
                f"Modelo spaCy '{self.model_name}' não encontrado. "
                "Instale-o executando: python -m pip install pt-core-news-sm "
                "ou: python -m spacy download pt_core_news_sm"
            )
            logger.exception(msg)
            raise RuntimeError(msg) from exc
        except Exception as exc:
            logger.exception("Erro ao carregar modelo spaCy '%s': %s", self.model_name, exc)
            raise

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extrai entidades do texto e retorna lista de dicionários:
        [{ "text": <entidade>, "label": <rótulo>, "start": <int>, "end": <int> }, ...]
        """
        if not self.nlp:
            raise RuntimeError("Modelo spaCy não carregado.")
        if not isinstance(text, str):
            raise TypeError("O parâmetro 'text' deve ser uma string.")
        doc = self.nlp(text)
        entities = [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]
        return entities

    def get_labels(self) -> List[str]:
        """Retorna a lista de rótulos (labels) conhecidos pelo modelo carregado."""
        if not self.nlp:
            raise RuntimeError("Modelo spaCy não carregado.")
        # Alguns modelos expõem nlp.pipe_labels ou nlp.get_pipe; usamos as entidades do vocab
        labels = list(self.nlp.get_pipe("ner").labels) if "ner" in self.nlp.pipe_names else []
        return labels

    def has_entities(self, text: str) -> bool:
        """Retorna True se o texto contiver ao menos uma entidade reconhecida."""
        ents = self.extract_entities(text)
        return len(ents) > 0


# Exemplo de uso (executar fora do módulo, p.ex. em um script de teste):
# from backend.models.entity_model import EntityExtractor
# extractor = EntityExtractor()
# print(extractor.extract_entities("João vai para São Paulo amanhã."))
#
# Observações de instalação:
# - Instale spaCy: python -m pip install spacy
# - Instale o modelo português (se ainda não tiver): python -m spacy download pt_core_news_sm
#
# Nota: em ambientes restritos (sem internet) instale o modelo manualmente antes de rodar.
__all__ = ["EntityExtractor"]
