import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt


def load_mnist():
    X, y = fetch_openml("mnist_784", version=1, return_X_y=True, as_frame=False, parser="auto")
    X = X.astype(np.float32) / 255.0
    y = y.astype(np.int64)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, y_train, X_test, y_test


def show_image(index, X, y):
    img = X[index].reshape(28, 28)
    plt.imshow(img, cmap="gray")
    plt.title(f"Label: {y[index]}")
    plt.axis("off")
    plt.show()


def one_hot_encode(y, num_classes=10):
    n = len(y)
    encoded = np.zeros((n, num_classes))
    encoded[np.arange(n), y] = 1
    return encoded
