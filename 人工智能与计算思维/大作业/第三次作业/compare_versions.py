import time
import numpy as np
from src.mlp import MLP
from src.data_utils import load_mnist
from src.dot_pure import dot_pure


def train_one_epoch(mlp, X_train, y_train, batch_size, learning_rate):
    n = X_train.shape[0]
    indices = np.random.permutation(n)
    for i in range(0, n, batch_size):
        batch_idx = indices[i:i + batch_size]
        x_batch = X_train[batch_idx]
        y_batch = y_train[batch_idx]
        logits = mlp.forward(x_batch)
        _ = mlp.loss_fn.forward(logits, y_batch)
        dout = mlp.loss_fn.backward()
        mlp.backward(dout)
        for layer in mlp.layers:
            if hasattr(layer, 'W'):
                layer.W -= learning_rate * layer.dW
                layer.b -= learning_rate * layer.db


def main():
    print("Loading MNIST (subset for speed)...")
    X_train, y_train, X_test, y_test = load_mnist()
    X_train = X_train[:5000]
    y_train = y_train[:5000]
    X_test = X_test[:1000]
    y_test = y_test[:1000]

    epochs = 3
    batch_size = 64
    learning_rate = 0.01

    # V1: numpy.dot
    print("\n=== V1: numpy.dot ===")
    mlp1 = MLP(layer_sizes=[784, 128, 64, 10])
    start1 = time.time()
    for ep in range(epochs):
        train_one_epoch(mlp1, X_train, y_train, batch_size, learning_rate)
    train_time1 = time.time() - start1
    start_pred = time.time()
    preds1 = mlp1.predict(X_test)
    pred_time1 = time.time() - start_pred

    # V2: pure Python dot
    print("\n=== V2: pure Python dot ===")
    import numpy
    original_dot = numpy.dot
    numpy.dot = dot_pure

    mlp2 = MLP(layer_sizes=[784, 128, 64, 10])
    start2 = time.time()
    for ep in range(epochs):
        train_one_epoch(mlp2, X_train, y_train, batch_size, learning_rate)
    train_time2 = time.time() - start2
    start_pred = time.time()
    preds2 = mlp2.predict(X_test)
    pred_time2 = time.time() - start_pred

    numpy.dot = original_dot

    # Results
    print("\n=== Comparison ===")
    print(f"{'Metric':<20} {'numpy.dot':<15} {'pure Python dot':<15} {'Ratio':<10}")
    print(f"{'Train time (s)':<20} {train_time1:<15.4f} {train_time2:<15.4f} {train_time2/train_time1:<10.2f}x")
    print(f"{'Predict time (s)':<20} {pred_time1:<15.4f} {pred_time2:<15.4f} {pred_time2/pred_time1:<10.2f}x")
    print(f"{'Test accuracy':<20} {np.mean(preds1==y_test):<15.4f} {np.mean(preds2==y_test):<15.4f} {'':<10}")


if __name__ == "__main__":
    main()
