import numpy as np
from src.dot_pure import dot_pure


def test_dot_pure_shape():
    A = np.random.randn(3, 4)
    B = np.random.randn(4, 5)
    C = dot_pure(A, B)
    assert C.shape == (3, 5)


def test_dot_pure_matches_numpy():
    A = np.random.randn(4, 6)
    B = np.random.randn(6, 3)
    C_pure = dot_pure(A, B)
    C_numpy = np.dot(A, B)
    assert np.allclose(C_pure, C_numpy, atol=1e-10)


def test_dot_pure_vector():
    A = np.random.randn(1, 5)
    B = np.random.randn(5, 1)
    C_pure = dot_pure(A, B)
    C_numpy = np.dot(A, B)
    assert np.allclose(C_pure, C_numpy, atol=1e-10)
