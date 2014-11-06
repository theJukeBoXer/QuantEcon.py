"""
Filename: gth_solve.py
Author: Daisuke Oyama

Tests for gth_solve.py

"""
from __future__ import division

import sys
import numpy as np
import nose
from nose.tools import eq_, ok_, raises

from quantecon.gth_solve import gth_solve


TOL = 1e-15


def KMR_Markov_matrix_sequential(N, p, epsilon):
    """
    Generate the Markov matrix for the KMR model with *sequential* move

    Parameters
    ----------
    N : int
        Number of players

    p : float
        Level of p-dominance of action 1, i.e.,
        the value of p such that action 1 is the BR for (1-q, q) for any q > p,
        where q (1-q, resp.) is the prob that the opponent plays action 1 (0, resp.)

    epsilon : float
        Probability of mutation

    Returns
    -------
    P : numpy.ndarray
        Markov matrix for the KMR model with simultaneous move

    """
    P = np.zeros((N+1, N+1), dtype=float)
    P[0, 0], P[0, 1] = 1 - epsilon * (1/2), epsilon * (1/2)
    for n in range(1, N):
        P[n, n-1] = \
            (n/N) * (epsilon * (1/2) +
                     (1 - epsilon) * (((n-1)/(N-1) < p) + ((n-1)/(N-1) == p) * (1/2))
                     )
        P[n, n+1] = \
            ((N-n)/N) * (epsilon * (1/2) +
                         (1 - epsilon) * ((n/(N-1) > p) + (n/(N-1) == p) * (1/2))
                         )
        P[n, n] = 1 - P[n, n-1] - P[n, n+1]
    P[N, N-1], P[N, N] = epsilon * (1/2), 1 - epsilon * (1/2)
    return P


class Matrices:
    """Setup matrices for the tests"""

    def __init__(self):
        self.stoch_matrix_dicts = []
        self.kmr_matrix_dicts = []
        self.gen_matrix_dicts = []

        matrix_dict = {
            'A': np.array([[0.4, 0.6], [0.2, 0.8]]),
            'stationary_dist': np.array([[0.25, 0.75]]),
        }
        self.stoch_matrix_dicts.append(matrix_dict)

        matrix_dict = {
            # Reducible matrix
            'A': np.array([[1, 0], [0, 1]]),
            # Stationary dist whose support contains index 0
            'stationary_dist': np.array([[1, 0]]),
        }
        self.stoch_matrix_dicts.append(matrix_dict)

        matrix_dict = {
            'A': KMR_Markov_matrix_sequential(N=27, p=1./3, epsilon=1e-2),
        }
        self.kmr_matrix_dicts.append(matrix_dict)

        matrix_dict = {
            'A': KMR_Markov_matrix_sequential(N=3, p=1./3, epsilon=1e-14),
        }
        self.kmr_matrix_dicts.append(matrix_dict)

        matrix_dict = {
            'A': np.array([[-1, 1], [4, -4]]),
            'stationary_dist': np.array([[0.8, 0.2]]),
        }
        self.gen_matrix_dicts.append(matrix_dict)


def test_stoch_matrix():
    """Test with stochastic matrices"""
    print(__name__ + '.' + test_stoch_matrix.__name__)
    matrices = Matrices()
    for matrix_dict in matrices.stoch_matrix_dicts:
        x = gth_solve(matrix_dict['A'])
        yield StationaryDistSumOne(), x
        yield StationaryDistNonnegative(), x
        yield StationaryDistEqualToKnown(), matrix_dict['stationary_dist'], x


def test_kmr_matrix():
    """Test with KMR matrices"""
    print(__name__ + '.' + test_kmr_matrix.__name__)
    matrices = Matrices()
    for matrix_dict in matrices.kmr_matrix_dicts:
        x = gth_solve(matrix_dict['A'])
        yield StationaryDistSumOne(), x
        yield StationaryDistNonnegative(), x
        yield StationaryDistLeftEigenVec(), matrix_dict['A'], x


def test_gen_solve():
    """Test with generator matrices"""
    print(__name__ + '.' + test_gen_solve.__name__)
    matrices = Matrices()
    for matrix_dict in matrices.gen_matrix_dicts:
        x = gth_solve(matrix_dict['A'])
        yield StationaryDistSumOne(), x
        yield StationaryDistNonnegative(), x
        yield StationaryDistEqualToKnown(), matrix_dict['stationary_dist'], x


class AddDescription:
    def __init__(self):
        self.description = self.__class__.__name__


class StationaryDistSumOne(AddDescription):
    def __call__(self, x):
        ok_(np.allclose(sum(x), 1, atol=TOL))


class StationaryDistNonnegative(AddDescription):
    def __call__(self, x):
        eq_(np.prod(x >= 0-TOL), 1)


class StationaryDistLeftEigenVec(AddDescription):
    def __call__(self, A, x):
        ok_(np.allclose(np.dot(x, A), x, atol=TOL))


class StationaryDistEqualToKnown(AddDescription):
    def __call__(self, y, x):
        ok_(np.allclose(y, x, atol=TOL))


@raises(ValueError)
def test_raises_value_error_non_2dim():
    """Test with non 2dim input"""
    gth_solve(np.array([0.4, 0.6]))


@raises(ValueError)
def test_raises_value_error_non_sym():
    """Test with non symmetric input"""
    gth_solve(np.array([[0.4, 0.6]]))


if __name__ == '__main__':
    argv = sys.argv[:]
    argv.append('--verbose')
    argv.append('--nocapture')
    nose.main(argv=argv, defaultTest=__file__)