import time
import numpy as np
from src.mlp import MLP
from src.data_utils import load_mnist


def main():
    print("Loading MNIST data...")
    X_train, y_train, X_test, y_test = load_mnist()
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")

    mlp = MLP(layer_sizes=[784, 128, 64, 10])

    epochs = 10
    batch_size = 64
    learning_rate = 0.01

    print(f"Training MLP: {epochs} epochs, batch_size={batch_size}, lr={learning_rate}")
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

        avg_loss = total_loss / n_batches
        train_pred = mlp.predict(X_train)
        train_acc = np.mean(train_pred == y_train)
        test_pred = mlp.predict(X_test)
        test_acc = np.mean(test_pred == y_test)
        print(f"Epoch {epoch + 1}/{epochs} | Loss: {avg_loss:.4f} | "
              f"Train Acc: {train_acc:.4f} | Test Acc: {test_acc:.4f}")

    elapsed = time.time() - start
    print(f"Training time: {elapsed:.2f}s")

    mlp.save("models/mnist_mlp.npz")
    print("Model saved to models/mnist_mlp.npz")

    with open("models/train_time_v1.txt", "w") as f:
        f.write(str(elapsed))


if __name__ == "__main__":
    main()
