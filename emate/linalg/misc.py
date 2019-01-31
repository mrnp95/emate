from scipy import sparse


def get_bounds(
    H,
    M=None,
    sigma=None,
    v0=None,
    ncv=None,
    maxiter=None,
    tol=0,
    Minv=None,
    OPinv=None,
    mode='normal'
):
    """
    This function gives the smallest and the largest eigenvalue associated with
    a Hermitian matrix H. For this purpose this function uses the scipy
    function. Therefore, you should give a look in the documentation of
    .. _sparse.linalg.eigsh: https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigsh.html


    Args:
        H: (scipy sparse matrix) A hermitian matrix in sparse format

    Return:
        lmin: (float) smallest eigenvalue
        lmax: (float) largest eigenvalue

    """
    lmax = float(
        sparse.linalg.eigsh(
            H,
            k=1,
            which="LA",
            return_eigenvectors=False,
            M=M,
            sigma=sigma,
            v0=v0,
            ncv=ncv,
            maxiter=maxiter,
            tol=tol,
            Minv=Minv,
            OPinv=OPinv,
            mode=mode
        )
    )
    lmin = float(
        sparse.linalg.eigsh(
                H,
                k=1,
                which="SA",
                return_eigenvectors=False,
                M=M,
                sigma=sigma,
                v0=v0,
                ncv=ncv,
                maxiter=maxiter,
                tol=tol,
                Minv=Minv,
                OPinv=OPinv,
                mode=mode
        )
    )

    return lmin, lmax


def rescale_matrix(H, lmin, lmax, epsilon=0.01):
    """
    Return a  rescaled H matrix, so that  the eigenvalues associated
are in the range $[-1, 1]$.

    Args:
        H: (scipy sparse matrix) A hermitian matrix in sparse format
        lmin: (float)
        lmax: (float)
        epsilon: (float)
    Return:
        H: (scipy sparse matrix) with eigenvalues  $\in [-1, 1]$
        scale_fact_a: (float)
        scale_fact_b: (float)

    """
    if (lmin is None) or (lmax is None):
        lmin, lmax = get_bounds(H)

    dimension = H.shape[0]
    scale_fact_a = (lmax - lmin) / (2. - epsilon)
    scale_fact_b = (lmax + lmin) / 2
    H_rescaled = (1/scale_fact_a)*(H-1*scale_fact_b*sparse.eye(dimension))

    return H_rescaled, scale_fact_a, scale_fact_b