import numpy as np


class CrossEntropyLoss:
    def __init__(self):
        self.probs = None
        self.targets = None

    def forward(self, logits, targets):
        shifted = logits - np.max(logits, axis=1, keepdims=True)
        exp_x = np.exp(shifted)
        self.probs = exp_x / np.sum(exp_x, axis=1, keepdims=True)
        self.targets = targets
        n = logits.shape[0]
        loss = -np.sum(np.log(self.probs[np.arange(n), targets] + 1e-8)) / n
        return loss

    def backward(self):
        n = self.probs.shape[0]
        dlogits = self.probs.copy()
        dlogits[np.arange(n), self.targets] -= 1
        dlogits /= n
        return dlogits
