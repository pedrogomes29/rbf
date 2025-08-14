#!/usr/bin/env python3
import unittest
from search_params import search_params
import params


class TestSerachParams(unittest.TestCase):
    def setUp(self):
        self.py_search = search_params()
        self.cpp_search_ptr = params.new()

    def test_bf_num_bytes(self):
        """Test the API bf_num_bytes"""
        error_cap_pairs = [
            (0.01, 10000),
            (0.01, 20000),
            (0.01, 30000),
            (0.1, 40000),
            (0.01, 50000),
            (0.02, 60000),
            (0.03, 89000),
            (0.05, 1000000),
        ]
        for error, cap in error_cap_pairs:
            py_ret = self.py_search.bf_num_bytes(error, cap)
            cpp_ret = params.bf_num_bytes(self.cpp_search_ptr, error, cap)
            print(f"py: {py_ret} | cpp: {cpp_ret}")
            self.assertAlmostEqual(py_ret, cpp_ret)

    def test_total(self):
        """Test the API total"""
        # a, fpr, n, y
        args_tuples = [
            (100, 0.01, 10000, 30),
            (20, 0.02, 10000, 20),
            (40, 0.03, 200000, 10),
            (3, 0.3, 1000, 7),
            (9, 0.05, 5000, 399),
            (57, 0.09, 4500, 13),
        ]

        for a, fpr, n, y in args_tuples:
            py_tot, py_rows = self.py_search.total(a, fpr, n, y)
            cpp_tot, cpp_rows = params.total(self.cpp_search_ptr, a, fpr, n, y)
            print(f"py: {py_tot}, {py_rows} | cpp: {cpp_tot}, {cpp_rows}")
            self.assertAlmostEqual(py_tot, cpp_tot)
            self.assertEqual(py_rows, cpp_rows)

    def test_solve_a(self):
        """Test API solve_a"""
        args = [
            (2000, 1000, 100, 50),
            (20000, 10000, 900, 100),
            (3000, 400, 98, 17),
            (90000, 7899, 99, 33),
            (12345, 567, 67, 91),
        ]

        for m, n, x, y in args:
            py_min_a, py_min_fpr, py_min_iblt_rows = self.py_search.solve_a(m, n, x, y)
            cpp_min_a, cpp_min_fpr, cpp_min_iblt_rows = params.solve_a(
                self.cpp_search_ptr, m, n, x, y
            )
            print(
                f"py: {py_min_a}, {py_min_fpr}, {py_min_iblt_rows} | cpp: {cpp_min_a}, {cpp_min_fpr}, {cpp_min_iblt_rows}"
            )
            self.assertAlmostEqual(py_min_a, cpp_min_a)
            self.assertAlmostEqual(py_min_fpr, cpp_min_fpr)
            self.assertEqual(py_min_iblt_rows, cpp_min_iblt_rows)

    def test_CB_bound(self):
        """Test API CB_bound"""
        args = [
            (100, 0.01, 239.0/240.0),
            (200, 0.3, 0.99),
            (59, 0.04, 0.98),
            (789, 0.05, 0.95),
            (345, 0.02, 0.9),
            (458, 0.4, 0.8)
        ]

        for a, fpr, bound in args:
            py_ret = self.py_search.CB_bound(a, fpr, bound)
            cpp_ret = params.CB_bound(self.cpp_search_ptr, a, fpr, bound)
            print(f"py: {py_ret} | cpp: {cpp_ret}")
            self.assertAlmostEqual(py_ret, cpp_ret)

    def test_CB_solve_a(self):
        """Test API CB_solve_a"""
        args = [
            (2000, 1000, 100, 50, 0.99),
            (20000, 10000, 900, 100, 0.995),
            (3000, 400, 98, 17, 0.9),
            (90000, 7899, 99, 33, 0.98),
            (12345, 567, 67, 91, 0.95),
        ]

        for m, n, x, y, bound in args:
            py_min_a, py_min_fpr, py_min_iblt_rows = self.py_search.CB_solve_a(m, n, x, y, bound)
            cpp_min_a, cpp_min_fpr, cpp_min_iblt_rows = params.CB_solve_a(
                self.cpp_search_ptr, m, n, x, y, bound
            )
            print(
                f"py: {py_min_a}, {py_min_fpr}, {py_min_iblt_rows} | cpp: {cpp_min_a}, {cpp_min_fpr}, {cpp_min_iblt_rows}"
            )
            self.assertAlmostEqual(py_min_a, cpp_min_a)
            self.assertAlmostEqual(py_min_fpr, cpp_min_fpr)
            self.assertEqual(py_min_iblt_rows, cpp_min_iblt_rows)

    def test_compute_delta(self):
        """Test API compute_delta"""
        # z, x, m, fpr
        args = [
            (100, 40, 1000, 0.01),
            (200, 50, 2000, 0.03),
            (400, 39, 10000, 0.1),
            (500, 45, 100000, 0.09),
            (345, 234, 50000, 0.07)
        ]

        for z,x,m,fpr in args:
            py_ret = self.py_search.compute_delta(z, x, m, fpr)
            cpp_ret = params.compute_delta(self.cpp_search_ptr, z, x, m, fpr)
            print(f"py: {py_ret} | cpp: {cpp_ret}")
            self.assertAlmostEqual(py_ret, cpp_ret)

    def test_compute_RHS(self):
        """Test API compute_RHS"""
        args = [
            (0.2, 100, 40, 0.01),
            (0.3, 200, 50, 0.03),
            (0.05, 400, 39, 0.1),
            (0.1, 500, 45, 0.09),
            (0.08, 345, 234, 0.07)
        ]    
        for delta, m, x, fpr in args:
            py_ret = self.py_search.compute_RHS(delta, m, x, fpr)
            cpp_ret = params.compute_RHS(self.cpp_search_ptr, delta, m, x, fpr)
            print(f"py: {py_ret} | cpp: {cpp_ret}")
            self.assertAlmostEqual(py_ret, cpp_ret)   

    def test_compute_binomial_prob(self):
        """Test API compute_binomial_prob"""
        # z, x, m, fpr
        args = [
            (109, 100, 100, 0.01),
            (210, 199, 200, 0.03),
            (104, 99, 100, 0.1),
            (211, 197, 200, 0.09),
            (503, 495, 500, 0.07)
        ]

        for z,x,m,fpr in args:
            py_ret = self.py_search.compute_binomial_prob(z, x, m, fpr)
            cpp_ret = params.compute_binomial_prob(self.cpp_search_ptr, z, x, m, fpr)
            print(f"py: {py_ret} | cpp: {cpp_ret}")
            self.assertAlmostEqual(py_ret, cpp_ret)
    
    def test_search_x_star(self):
        """Test API search_x_star"""
        # z, mempool_size, fpr, bound, blk_size
        args = [
            (109, 200, 0.01, 0.995, 100),
            (211, 300, 0.07, 0.9, 200),
            (304, 500, 0.1, 0.95, 297),
            (411, 600, 0.05, 0.975, 400),
            (503, 1000, 0.6, 0.97, 495)
        ]

        for z, mempool_size, fpr, bound, blk_size in args:
            py_ret = self.py_search.search_x_star(z, mempool_size, fpr, bound, blk_size)
            cpp_ret = params.search_x_star(self.cpp_search_ptr, z, mempool_size, fpr, bound, blk_size)
            print(f"py: {py_ret} | cpp: {cpp_ret}")
            self.assertEqual(py_ret, cpp_ret)


    def tearDown(self):
        params.delete(self.cpp_search_ptr)


if __name__ == "__main__":
    unittest.main(verbosity=4)
