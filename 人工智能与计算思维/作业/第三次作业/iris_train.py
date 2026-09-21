# iris_train.py
import time
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from src.mlp import MLP


def main():
    print("Loading Iris dataset...")
    X, y = load_iris(return_X_y=True)
    X = X.astype(np.float32)
    X = (X - X.mean(axis=0)) / X.std(axis=0)
    y = y.astype(np.int64)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    print(f"Features: {X.shape[1]}, Classes: {len(np.unique(y))}")
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")

    mlp = MLP(layer_sizes=[4, 32, 16, 3])

    epochs = 100
    batch_size = 8
    learning_rate = 0.01

    print(f"Training: {epochs} epochs, batch_size={batch_size}, lr={learning_rate}")
    start = time.time()

    n = X_train.shape[0]
    for epoch in range(epochs):
        indices = np.random.permutation(n)
        total_loss = 0
        n_batches = 0
        for i in range(0, n, batch_size):
            batch_idx = indices[i:i + batch_size]
            x_batch = X_train[batch_idx]
            y_batch = y_train[batch_idx]

            logits = mlp.forward(x_batch)
            loss = mlp.loss_fn.forward(logits, y_batch)
            total_loss += loss
            n_batches += 1

            dout = mlp.loss_fn.backward()
            mlp.backward(dout)

            for layer in mlp.layers:
                if hasattr(layer, 'W'):
                    layer.W -= learning_rate * layer.dW
                    layer.b -= learning_rate * layer.db

        if (epoch + 1) % 20 == 0:
            train_pred = mlp.predict(X_train)
            test_pred = mlp.predict(X_test)
            print(f"Epoch {epoch + 1}/{epochs} | Loss: {total_loss / n_batches:.4f} | "
                  f"Train Acc: {np.mean(train_pred == y_train):.4f} | "
                  f"Test Acc: {np.mean(test_pred == y_test):.4f}")

    elapsed = time.time() - start
    print(f"Training time: {elapsed:.2f}s")

    mlp.save("models/iris_mlp.npz")
    print("Model saved to models/iris_mlp.npz")


if __name__ == "__main__":
    main()
