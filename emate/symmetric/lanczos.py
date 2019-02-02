"""
Lanczos
=======


Available methods
-----------------

trace_estimator


"""

import tensorflow as tf
import numpy as np

from emate.utils.vector_factories import radamacher
from emate.linalg.lanczos import lanczos
from emate.utils import replace_by_indices


def trace_estimator(
    A,
    dimension,
    num_vecs,
    num_steps,
    trace_function,
    random_factory=radamacher,
    parallel_iterations=10,
    swap_memory=False,
    infer_shape=False,
    tf_float=tf.float32,
    name_scope=None
):
    """

    This function estimate the trace of a given matrix function (trace_function)
    through stochastic Lanczos quadrature. Read more in
    .. _Fast Estimation of $tr(f(A))$ via Stochastic Lanczos Quadrature:
        https://epubs.siam.org/doi/abs/10.1137/16M1104974

    Parameters
    ----------
        A,
        dimension,
        num_vecs,
        num_steps,
        trace_function,
        random_factory=radamacher,
        parallel_iterations=10,
        swap_memory=False,
        infer_shape=False,
        tf_type: (tensorflow float type)(default=tf.float32)
        name_scope: (str)(default="replace_by_indices")
            scope name for tensorflow

    Returns
    -------
        output_matrix: Tensor(shape=(dimension, dimension), dtype=tf_type)
    """
    with tf.name_scope("Trace_Estimator"):
        with tf.name_scope("init_vars"):
            nv = tf.constant(num_vecs, dtype=tf_float, name="nv")
            n = tf.constant(dimension, dtype=tf_float, name="n")
            factor = tf.divide(n, nv, "n/nv")
        with tf.name_scope("sthocastic_step"):
            def sthocastic_step(i_step):
                with tf.name_scope("init_vars"):
                    v0 = random_factory((dimension, 1), tf_float)

                V, alphas, betas, ortho_ok, num_alphas = lanczos(
                    A, dimension, v0, num_steps)

                with tf.name_scope("construct_tridiagonal"):
                    T = tf.diag(alphas,)

                    row_idx = tf.range(0, num_alphas-1, dtype=tf.int64)
                    col_idx = tf.range(1, num_alphas, dtype=tf.int64)

                    above_idx = tf.stack([row_idx, col_idx], axis=-1)
                    below_idx = tf.stack([col_idx, row_idx], axis=-1)

                    indices = tf.concat([above_idx, below_idx], axis=0)
                    values = tf.concat([betas, betas], axis=0)

                    T = replace_by_indices(T, values, indices, tf_float)

                eigvals, eigvecs = tf.linalg.eigh(T)
                thetas = trace_function(eigvals)
                tau2 = tf.math.pow(tf.gather(eigvecs, 0), 2)

                gamma = tf.reduce_sum(
                    tf.math.multiply(
                        tau2,
                        thetas
                    ),
                    axis=0
                )
                return gamma

    gammas = tf.map_fn(
        sthocastic_step,
        np.arange(0, num_vecs),
        dtype=(tf_float),
        parallel_iterations=parallel_iterations,
        swap_memory=swap_memory,
        infer_shape=infer_shape,
        name="map_gammas_sthocastic_step"
    )

    f_estimation = tf.reduce_sum(
        factor*gammas, axis=0, name="f_estimation"
    )
    return f_estimation, gammas