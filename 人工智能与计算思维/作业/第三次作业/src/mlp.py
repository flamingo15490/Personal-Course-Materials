import numpy as np
from src.layers import Dense, ReLU, Softmax
from src.losses import CrossEntropyLoss


class MLP:
    def __init__(self, layer_sizes):
        self.layers = []
        for i in range(len(layer_sizes) - 1):
            self.layers.append(Dense(layer_sizes[i], layer_sizes[i + 1]))
            if i < len(layer_sizes) - 2:
                self.layers.append(ReLU())
        self.softmax = Softmax()
        self.loss_fn = CrossEntropyLoss()

    def forward(self, x):
        """Return raw logits (no softmax). CE loss handles softmax internally."""
        out = x
        for layer in self.layers:
            out = layer.forward(out)
        return out

    def backward(self, dout):
        """Backward pass through all layers. dout is gradient from CE loss."""
        d = dout
        for layer in reversed(self.layers):
            d = layer.backward(d)
        return d

    def predict(self, x):
        """Return class predictions. Applies softmax to logits."""
        logits = self.forward(x)
        probs = self.softmax.forward(logits)
        return np.argmax(probs, axis=1)

    def save(self, filepath):
        params = {}
        dense_idx = 0
        for layer in self.layers:
            if isinstance(layer, Dense):
                params[f"W{dense_idx}"] = layer.W
                params[f"b{dense_idx}"] = layer.b
                dense_idx += 1
        np.savez(filepath, **params)

    def load(self, filepath):
        data = np.load(filepath)
        dense_idx = 0
        for layer in self.layers:
            if isinstance(layer, Dense):
                layer.W = data[f"W{dense_idx}"]
                layer.b = data[f"b{dense_idx}"]
                dense_idx += 1
