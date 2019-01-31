import tensorflow as tf

def apply_lanczos_step(
    beta,
    wn,
    v,
    vold,
    V,
    A,
    name_scope=None
):
    with tf.name_scope(name_scope, "lanczos_step") as scope:

        w = tf.subtract(
            tf.sparse_tensor_dense_matmul(A, v),
            beta*vold,
            name="w"
        )

        alpha = tf.reshape(
            tf.tensordot(w, v, axes=[(0, 1), (0, 1)]),
            [1],
            name="alpha"
        )

        wn = tf.reshape(
            tf.add(wn, alpha*alpha),
            [1],
            name="wn"
        )

        w = tf.subtract(w, alpha*v, name="w")

        t = tf.linalg.matmul(
            tf.transpose(V),
            w,
            name="t"
        )

        w = tf.subtract(
            w,
            tf.linalg.matmul(V, t),
            name="w"
        )

        beta = tf.reduce_sum(
            tf.math.pow(w, 2),
            axis=0,
            name="beta"
        )

    return alpha, beta, wn, w, t



def lanczos_ortho_fail(alpha, beta, w, wn, vold, v, V, alphas, betas):
    with tf.name_scope("ortho_fail") as scope:
        return [alpha, beta, wn, vold, v, V,tf.concat([alphas, alpha], axis=0), betas,  False]

def lanczos_ortho_ok(alpha, beta, w, wn, vold, v, V, alphas, betas):
    with tf.name_scope("ortho_ok") as scope:
        wn = wn+2.0*beta
        beta = tf.sqrt(beta)
        vold = v
        v = w/beta

        return [
            alpha,
            beta,
            wn,
            vold,
            v,
            tf.concat([ V, v], axis=1),
            tf.concat([alphas, alpha], axis=0),
            tf.concat([betas, beta], axis=0),
            tf.constant(True, dtype=tf.bool)
        ]

def lanczos(A, dimension, v0, num_steps, tf_float=tf.float32, orth_tol=10e-08):
    with tf.name_scope("Lanczos_Method") as scope:

        with tf.name_scope("init_vars") as scope:
            alpha =  tf.constant([0], dtype=tf_float, name="alpha")
            beta =  tf.constant([0], dtype=tf_float, name="beta")
            wn =  tf.constant([0], dtype=tf_float, name="wn")
            alphas = tf.constant([], dtype=tf_float, name="list_alphas")
            betas = tf.constant([], dtype=tf_float, name="list_betas")
            i_step = tf.constant(0, name="i_step")
            num_steps = tf.constant(num_steps, name="num_steps")
            ortho_ok = tf.constant(True, dtype=tf.bool, name="ortho_ok")
            orth_tol = tf.constant([orth_tol], name="ortho_tolerance")

            v  =  v0/tf.linalg.norm(v0, 2, name="v")


        def cond(alpha, beta,  wn, v, vold, V, alphas, betas, ortho_ok, i_step):
            with tf.name_scope("while_cond") as scope:

                return tf.logical_and(
                    tf.less(i_step, num_steps),
                    ortho_ok
                )

        def body(alpha, beta, wn, v, vold, V, alphas, betas, ortho_ok, i_step):
            with tf.name_scope("while_body") as scope:

                alpha, beta, wn, w, t = apply_lanczos_step(beta, wn, v, vold, V, A)

                with tf.name_scope("ortho_condition", values=[beta, i_step]) as scope:
                    break_condition = tf.logical_and(
                        tf.less(
                            (wn*orth_tol)[0], (beta*tf.cast(i_step, dtype=tf.float32))[0],
                            name="break_condition"
                        ),
                        tf.less_equal(i_step, num_steps)
                    )
                    alpha, beta, wn, vold, v, V, alphas, betas, ortho_ok = tf.cond(
                        pred = break_condition,
                        true_fn = lambda:lanczos_ortho_ok(alpha, beta, w, wn, vold, v, V, alphas, betas),
                        false_fn = lambda: lanczos_ortho_fail(alpha, beta, w, wn, vold, v, V, alphas, betas),
                        name="conditional"
                    )

                return [alpha, beta, wn, v, vold, V, alphas, betas, ortho_ok, tf.add(i_step,1)]


        alpha, beta, wn, v, vold, V, alphas, betas, ortho_ok, i_step = tf.while_loop(
            cond = cond,
            body = body,
            loop_vars = [alpha, beta, wn, v, v, v, alphas, betas, ortho_ok, i_step],
            shape_invariants=[
                alpha.get_shape(),
                beta.get_shape(),
                wn.get_shape(),
                v.get_shape(),
                v.get_shape(),
                tf.TensorShape([dimension, None]),
                tf.TensorShape([None]),
                tf.TensorShape([None]),
                ortho_ok.get_shape(),
                i_step.get_shape(),
            ],
            name="while_iterations"
        )

        return V, alphas, betas, ortho_ok
