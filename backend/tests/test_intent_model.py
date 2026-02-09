# tests/test_intent_model.py
import os
import tempfile
from backend.models.intent_model import IntentClassifier
import pytest


def make_sample_data():
    texts = [
        "tocar música",
        "abrir navegador",
        "qual é o tempo hoje",
        "tocar minha playlist",
        "abrir o chrome",
        "como está o tempo",
    ]
    labels = [
        "tocar_audio",
        "abrir_app",
        "consultar_tempo",
        "tocar_audio",
        "abrir_app",
        "consultar_tempo",
    ]
    return texts, labels


def test_train_predict_and_info(tmp_path):
    texts, labels = make_sample_data()
    clf = IntentClassifier()
    metrics = clf.train(texts, labels, test_size=0.5, random_state=1)
    assert isinstance(metrics, dict)
    assert clf.is_trained is True

    # predict returns string
    pred = clf.predict("quero ouvir uma música")
    assert isinstance(pred, str)
    assert pred in {"tocar_audio", "abrir_app", "consultar_tempo"}

    # predict_proba returns tuple (str, float)
    label, prob = clf.predict_proba("quero ouvir uma música")
    assert isinstance(label, str)
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0

    info = clf.info()
    assert isinstance(info, dict)
    assert info.get("is_trained") is True
    # classes pode ser None ou lista
    classes = info.get("classes")
    assert classes is None or isinstance(classes, list)


def test_save_and_load(tmp_path):
    texts, labels = make_sample_data()
    clf = IntentClassifier()
    clf.train(texts, labels, test_size=0.5, random_state=1)

    model_path = tmp_path / "intent_model.joblib"
    clf.save(str(model_path))
    assert model_path.exists()

    clf2 = IntentClassifier()
    clf2.load(str(model_path))
    assert clf2.is_trained is True

    pred = clf2.predict("abrir o navegador")
    assert isinstance(pred, str)
