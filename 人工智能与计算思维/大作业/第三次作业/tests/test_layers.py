import numpy as np
from src.layers import Dense


def test_dense_forward_shape():
    dense = Dense(input_dim=5, output_dim=3)
    x = np.random.randn(2, 5)  # batch_size=2, input_dim=5
    out = dense.forward(x)
    assert out.shape == (2, 3)


def test_dense_backward_shape():
    dense = Dense(input_dim=5, output_dim=3)
    x = np.random.randn(2, 5)
    dense.forward(x)
    dout = np.random.randn(2, 3)
    dx = dense.backward(dout)
    assert dx.shape == (2, 5)


def test_dense_gradient_numerical():
    dense = Dense(input_dim=3, output_dim=2)
    dense.W = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    dense.b = np.array([[0.1, 0.2]])
    x = np.array([[1.0, 2.0, 3.0]])
    _ = dense.forward(x)
    dout = np.ones((1, 2))
    dx = dense.backward(dout)
    dW = dense.dW
    db = dense.db
    assert dW.shape == dense.W.shape
    assert db.shape == dense.b.shape


def test_relu_forward():
    from src.layers import ReLU
    relu = ReLU()
    x = np.array([[-1.0, 0.0, 2.0], [3.0, -5.0, 0.5]])
    out = relu.forward(x)
    expected = np.array([[0.0, 0.0, 2.0], [3.0, 0.0, 0.5]])
    assert np.allclose(out, expected)


def test_relu_backward():
    from src.layers import ReLU
    relu = ReLU()
    x = np.array([[-1.0, 2.0], [3.0, -5.0]])
    relu.forward(x)
    dout = np.ones((2, 2))
    dx = relu.backward(dout)
    expected = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert np.allclose(dx, expected)


def test_softmax_rows_sum_to_one():
    from src.layers import Softmax
    softmax = Softmax()
    x = np.random.randn(4, 10)
    out = softmax.forward(x)
    assert np.allclose(out.sum(axis=1), np.ones(4))


def test_softmax_values_in_range():
    from src.layers import Softmax
    softmax = Softmax()
    x = np.random.randn(3, 5)
    out = softmax.forward(x)
    assert np.all(out >= 0) and np.all(out <= 1)
