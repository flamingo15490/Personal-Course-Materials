import numpy as np
from src.mlp import MLP


def test_mlp_forward_shape():
    mlp = MLP(layer_sizes=[784, 128, 64, 10])
    x = np.random.randn(32, 784)
    logits = mlp.forward(x)
    assert logits.shape == (32, 10)


def test_mlp_predict_shape():
    mlp = MLP(layer_sizes=[784, 128, 64, 10])
    x = np.random.randn(16, 784)
    preds = mlp.predict(x)
    assert preds.shape == (16,)
    assert np.all((preds >= 0) & (preds < 10))


def test_mlp_save_load():
    mlp = MLP(layer_sizes=[10, 8, 5])
    mlp.save("models/test_mlp.npz")
    mlp2 = MLP(layer_sizes=[10, 8, 5])
    mlp2.load("models/test_mlp.npz")
    x = np.random.randn(4, 10)
    assert np.allclose(mlp.predict(x), mlp2.predict(x))
