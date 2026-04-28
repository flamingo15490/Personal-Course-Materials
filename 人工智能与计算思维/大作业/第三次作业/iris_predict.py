# iris_predict.py
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from src.mlp import MLP
from src.metrics import compute_confusion_matrix, precision_recall_f1


def main():
    print("Loading Iris dataset...")
    X, y = load_iris(return_X_y=True)
    X = X.astype(np.float32)
    X = (X - X.mean(axis=0)) / X.std(axis=0)
    y = y.astype(np.int64)
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    mlp = MLP(layer_sizes=[4, 32, 16, 3])
    mlp.load("models/iris_mlp.npz")
    print("Model loaded from models/iris_mlp.npz")

    preds = mlp.predict(X_test)
    test_acc = np.mean(preds == y_test)
    print(f"Test Accuracy: {test_acc:.4f}")

    cm = compute_confusion_matrix(y_test, preds, num_classes=3)
    iris_names = ["setosa", "versicolor", "virginica"]
    print("\nConfusion Matrix:")
    print("           " + " ".join(f"{n:<12}" for n in iris_names))
    for i in range(3):
        print(f"  {iris_names[i]:<10} " + " ".join(f"{cm[i, j]:<12}" for j in range(3)))

    result = precision_recall_f1(y_test, preds, num_classes=3)
    print("\nPer-class Precision / Recall / F1:")
    print(f"{'Class':<12} {'Precision':<10} {'Recall':<10} {'F1':<10}")
    for c in range(3):
        print(f"{iris_names[c]:<12} {result['precision'][c]:<10.4f} "
              f"{result['recall'][c]:<10.4f} {result['f1'][c]:<10.4f}")
    print(f"\nMacro-avg F1: {np.mean(result['f1']):.4f}")


if __name__ == "__main__":
    main()
