import numpy as np


def dot_pure(A, B):
    m, k1 = A.shape
    k2, n = B.shape
    if k1 != k2:
        raise ValueError(f"Shape mismatch: ({m},{k1}) x ({k2},{n})")
    C = np.zeros((m, n))
    for i in range(m):
        for j in range(n):
            s = 0.0
            for t in range(k1):
                s += A[i, t] * B[t, j]
            C[i, j] = s
    return C
