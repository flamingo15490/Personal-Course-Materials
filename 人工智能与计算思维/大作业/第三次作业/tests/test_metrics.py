# tests/test_metrics.py
import numpy as np
from src.metrics import compute_confusion_matrix, precision_recall_f1


def test_confusion_matrix():
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 1, 2, 0])
    cm = compute_confusion_matrix(y_true, y_pred, num_classes=3)
    expected = np.array([
        [1, 1, 0],
        [0, 2, 0],
        [1, 0, 1]
    ])
    assert np.array_equal(cm, expected)


def test_precision_recall_f1():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_pred = np.array([0, 1, 0, 1, 1, 0])
    result = precision_recall_f1(y_true, y_pred, num_classes=2)
    assert "precision" in result
    assert "recall" in result
    assert "f1" in result
    assert len(result["precision"]) == 2
    assert 0 <= result["f1"][0] <= 1
