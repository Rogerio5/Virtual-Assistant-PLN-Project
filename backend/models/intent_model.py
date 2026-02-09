# backend/models/intent_model.py
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import os
import joblib
import logging

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

logger = logging.getLogger(__name__)


@dataclass
class ModelMeta:
    version: str
    labels: Optional[List[str]] = None
    trained_at: Optional[str] = None
    params: Optional[dict] = None


class IntentClassifier:
    """
    Classificador de intents baseado em TF-IDF + LogisticRegression.
    Usa Pipeline e joblib para persistência.
    """

    def __init__(
        self,
        ngram_range: Tuple[int, int] = (1, 2),
        max_features: Optional[int] = 20000,
        C: float = 1.0,
        random_state: int = 42,
    ):
        self.pipeline: Pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        lowercase=True,
                        strip_accents="unicode",
                        ngram_range=ngram_range,
                        max_features=max_features,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=C,
                        max_iter=1000,
                        random_state=random_state,
                        class_weight="balanced",
                    ),
                ),
            ]
        )
        self.meta: Optional[ModelMeta] = None
        self.is_trained: bool = False

    def train(self, texts: List[str], labels: List[str], test_size: float = 0.2, random_state: int = 42) -> dict:
        """
        Treina o modelo e retorna métricas no conjunto de validação.
        """
        if not texts or not labels or len(texts) != len(labels):
            raise ValueError("texts e labels devem ser listas não vazias e do mesmo tamanho.")

        stratify_arg = labels if len(set(labels)) > 1 else None
        X_train, X_val, y_train, y_val = train_test_split(
            texts, labels, test_size=test_size, random_state=random_state, stratify=stratify_arg
        )
        self.pipeline.fit(X_train, y_train)
        self.is_trained = True

        preds = self.pipeline.predict(X_val)
        metrics = {
            "accuracy": float(accuracy_score(y_val, preds)),
            "f1": float(f1_score(y_val, preds, average="weighted", zero_division=0)),
            "precision": float(precision_score(y_val, preds, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_val, preds, average="weighted", zero_division=0)),
        }
        logger.info("Treinamento concluído. Métricas: %s", metrics)
        # populate meta
        try:
            import datetime

            labels_unique = sorted(list(set(labels)))
            self.meta = ModelMeta(
                version=datetime.datetime.utcnow().isoformat(),
                labels=labels_unique,
                trained_at=datetime.datetime.utcnow().isoformat(),
                params=self.pipeline.get_params(),
            )
        except Exception:
            self.meta = None
        return metrics

    def predict(self, text: str) -> str:
        """
        Retorna o rótulo predito como string.
        """
        if not self.is_trained:
            raise RuntimeError("Modelo não treinado. Chame train() ou load().")
        pred = self.pipeline.predict([text])[0]
        return str(pred)

    def predict_proba(self, text: str) -> Tuple[str, float]:
        """
        Retorna (label_predito, probabilidade_da_classe_predita).
        Faz fallback seguro caso predict_proba não exista ou tipos inesperados apareçam.
        """
        if not self.is_trained:
            raise RuntimeError("Modelo não treinado. Chame train() ou load().")

        # Se o pipeline não expõe predict_proba, retorna label via predict com prob 1.0
        predict_proba_fn = getattr(self.pipeline, "predict_proba", None)
        if not callable(predict_proba_fn):
            label = self.predict(text)
            return label, 1.0

        probs_raw = self.pipeline.predict_proba([text])
        # probs_raw pode ser ndarray 2D; extrair primeira linha com segurança
        try:
            probs = probs_raw[0]
        except Exception:
            # fallback: tente converter para lista
            try:
                probs = list(probs_raw)[0]
            except Exception:
                label = self.predict(text)
                return label, 1.0

        # determinar índice da maior probabilidade de forma robusta
        try:
            # numpy arrays têm argmax
            idx = int(probs.argmax())
        except Exception:
            try:
                # fallback puro Python
                idx = max(range(len(probs)), key=lambda i: float(probs[i]))
            except Exception:
                label = self.predict(text)
                return label, 1.0

        classes_attr = getattr(self.pipeline, "classes_", None)
        if classes_attr is None:
            label = self.predict(text)
        else:
            try:
                label = classes_attr[idx]
            except Exception:
                try:
                    # classes_attr pode ser ndarray ou tuple/list
                    if hasattr(classes_attr, "tolist"):
                        cls_list = classes_attr.tolist()
                        label = cls_list[idx]
                    else:
                        label = list(classes_attr)[idx]
                except Exception:
                    label = self.predict(text)

        try:
            prob_value = float(probs[idx])
        except Exception:
            prob_value = 1.0

        return str(label), prob_value

    def predict_batch(self, texts: List[str]) -> List[str]:
        if not self.is_trained:
            raise RuntimeError("Modelo não treinado. Chame train() ou load().")
        preds = self.pipeline.predict(texts)
        # garantir lista de strings
        return [str(p) for p in preds]

    def save(self, path: str = "models/intent_model.joblib") -> None:
        """
        Salva pipeline + meta em arquivo joblib.
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload = {"pipeline": self.pipeline, "meta": asdict(self.meta) if self.meta else None}
        joblib.dump(payload, path)
        logger.info("Modelo salvo em %s", path)

    def load(self, path: str = "models/intent_model.joblib") -> None:
        """
        Carrega pipeline + meta de arquivo joblib.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {path}")
        payload = joblib.load(path)
        self.pipeline = payload.get("pipeline", self.pipeline)
        meta_dict = payload.get("meta")
        if meta_dict:
            self.meta = ModelMeta(**meta_dict)
        self.is_trained = True
        logger.info("Modelo carregado de %s", path)

    def info(self) -> dict:
        """
        Retorna informações do modelo de forma segura para tipagem estática.
        """
        meta_dict = asdict(self.meta) if self.meta is not None else None

        classes_attr = getattr(self.pipeline, "classes_", None)
        classes_list: Optional[List[str]] = None
        if classes_attr is None:
            classes_list = None
        else:
            try:
                if hasattr(classes_attr, "tolist"):
                    classes_list = classes_attr.tolist()
                else:
                    classes_list = [str(c) for c in classes_attr]
            except Exception:
                try:
                    classes_list = list(classes_attr)
                except Exception:
                    classes_list = None

        return {
            "is_trained": self.is_trained,
            "meta": meta_dict,
            "classes": classes_list,
        }
