import numpy as np
from src.losses import CrossEntropyLoss


def test_ce_loss_known_values():
    criterion = CrossEntropyLoss()
    logits = np.array([[2.0, 1.0, 0.1], [0.5, 2.0, 0.5]])
    targets = np.array([0, 1])
    loss = criterion.forward(logits, targets)
    assert loss > 0


def test_ce_loss_perfect_prediction():
    criterion = CrossEntropyLoss()
    logits = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0]])
    targets = np.array([0, 1])
    loss = criterion.forward(logits, targets)
    assert loss < 0.01


def test_ce_backward_shape():
    criterion = CrossEntropyLoss()
    logits = np.random.randn(8, 10)
    targets = np.random.randint(0, 10, 8)
    criterion.forward(logits, targets)
    dlogits = criterion.backward()
    assert dlogits.shape == (8, 10)
