# backend/services/command_executor.py
import unicodedata
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger("command_executor")


def normalize(text: str) -> str:
    """
    Normaliza texto removendo acentos, convertendo para minúsculas e
    colapsando espaços. Retorna string segura para comparação.
    """
    if not isinstance(text, str):
        text = str(text or "")
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_bytes = nfkd.encode("ASCII", "ignore")
    cleaned = ascii_bytes.decode("utf-8")
    # remove caracteres não alfanuméricos exceto espaços e underscores
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # colapsa múltiplos espaços e trim
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


class CommandExecutor:
    """
    Executor simples de comandos baseado em correspondência por substring
    e regras heurísticas. Projetado para ser leve e facilmente extensível.
    """

    def __init__(self, intents: Optional[Dict[str, str]] = None):
        # Intenções padrão (chaves já normalizadas)
        default_intents = {
            "ola": "Olá! Estou bem, e você?",
            "tudo bem": "Olá! Estou bem, e você?",
            "piada": "Por que o computador foi ao médico? Porque estava com um vírus!",
            "capital franca": "A capital da França é Paris.",
            "traduz bom dia": "Bom dia em inglês é Good Morning.",
        }
        # Normalize keys of provided intents as well
        merged = default_intents.copy()
        if intents:
            for k, v in intents.items():
                merged[normalize(k)] = v
        self.intents = {normalize(k): v for k, v in merged.items()}

    def _match_intent(self, text_norm: str) -> Optional[str]:
        """
        Tenta encontrar uma resposta por correspondência de substring.
        Prioriza chaves mais longas para evitar matches parciais indesejados.
        """
        # Ordena por comprimento decrescente para priorizar frases mais específicas
        for key in sorted(self.intents.keys(), key=lambda s: -len(s)):
            if key and key in text_norm:
                logger.debug("Intent matched: %s", key)
                return self.intents[key]
        return None

    def _extract_wikipedia_topic(self, text_norm: str) -> str:
        """
        Extrai termo após a palavra 'wikipedia' ou retorna termo padrão.
        """
        parts = text_norm.split("wikipedia", 1)
        if len(parts) > 1:
            topic = parts[1].strip()
            topic = topic or "Inteligencia_artificial"
        else:
            # tenta extrair termo após 'wikiped' por segurança
            m = re.search(r"wikiped\w*\s+(.+)", text_norm)
            topic = (m.group(1).strip() if m else "Inteligencia_artificial")
        # normaliza underscores e capitalização mínima para URL
        topic = topic.replace(" ", "_")
        return topic

    def execute(self, text: str) -> Dict[str, Any]:
        """
        Executa um comando baseado no texto do usuário.
        Retorna dicionário com chaves:
          - response: str (mensagem para o usuário)
          - actions: dict (ações sugeridas, ex.: URLs)
        """
        text_norm = normalize(text)
        actions: Dict[str, str] = {}
        response: Optional[str] = None

        logger.info("Executando comando: %s", text_norm)

        # 1. Intenções diretas do dicionário
        response = self._match_intent(text_norm)

        # 2. Casos especiais com ações
        if response is None:
            if "leonardo" in text_norm and "musica" in text_norm:
                actions = {
                    "youtube": "https://www.youtube.com/results?search_query=Leonardo+sertanejo",
                    "spotify": "https://open.spotify.com/search/Leonardo",
                }
                response = "Claro! Vou procurar músicas do Leonardo para você. Quer abrir no YouTube ou Spotify?"

            elif "wikipedia" in text_norm:
                topic = self._extract_wikipedia_topic(text_norm)
                actions = {"wikipedia": f"https://pt.wikipedia.org/wiki/{topic}"}
                # human-friendly topic display
                display_topic = topic.replace("_", " ").capitalize()
                response = f"Abrindo a Wikipedia sobre {display_topic}."

            elif "clima" in text_norm or "previsao do tempo" in text_norm or "previsão do tempo" in text_norm:
                # Em produção, delegar para um serviço de clima; aqui resposta estática
                response = "A previsão do tempo para São Paulo hoje é de sol com algumas nuvens."

        # 3. Caso não tenha correspondência
        if response is None:
            response = "Desculpe, não entendi o comando. Pode repetir?"

        return {"response": response, "actions": actions}


# Instância global reutilizável
command_executor = CommandExecutor()
