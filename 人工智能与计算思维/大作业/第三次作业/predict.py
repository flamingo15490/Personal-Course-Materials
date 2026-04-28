# predict.py
import numpy as np
import matplotlib.pyplot as plt
from src.mlp import MLP
from src.data_utils import load_mnist, show_image
from src.metrics import compute_confusion_matrix, precision_recall_f1


def main():
    print("Loading MNIST data...")
    _, _, X_test, y_test = load_mnist()

    mlp = MLP(layer_sizes=[784, 128, 64, 10])
    mlp.load("models/mnist_mlp.npz")
    print("Model loaded from models/mnist_mlp.npz")

    preds = mlp.predict(X_test)
    test_acc = np.mean(preds == y_test)
    print(f"Test Accuracy: {test_acc:.4f}")

    cm = compute_confusion_matrix(y_test, preds, num_classes=10)
    print("\nConfusion Matrix:")
    print("     " + " ".join(f"{i:4d}" for i in range(10)))
    for i in range(10):
        print(f"  {i}: " + " ".join(f"{cm[i, j]:4d}" for j in range(10)))

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix")
    plt.colorbar(im)
    for i in range(10):
        for j in range(10):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8)
    plt.savefig("confusion_matrix.png", dpi=150)
    print("Confusion matrix saved to confusion_matrix.png")
    plt.show()

    result = precision_recall_f1(y_test, preds, num_classes=10)
    print("\nPer-class Precision / Recall / F1:")
    print(f"{'Digit':<6} {'Precision':<10} {'Recall':<10} {'F1':<10}")
    for c in range(10):
        print(f"{c:<6} {result['precision'][c]:<10.4f} {result['recall'][c]:<10.4f} {result['f1'][c]:<10.4f}")
    print(f"\nMacro-avg F1: {np.mean(result['f1']):.4f}")

    print("\nShowing sample image (index=0):")
    show_image(0, X_test, y_test)


if __name__ == "__main__":
    main()
