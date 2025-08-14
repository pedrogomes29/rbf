#define PY_SSIZE_T_CLEAN
#include "search_params.h"
#include <Python.h>

static PyObject *wrapper_params_new(PyObject *self, PyObject *args);
static PyObject *wrapper_params_bf_num_bytes(PyObject *self, PyObject *args);
static PyObject *wrapper_params_delete(PyObject *self, PyObject *args);
static PyObject *wrapper_params_total(PyObject *self, PyObject *args);
static PyObject *wrapper_params_solve_a(PyObject *self, PyObject *args);
static PyObject *wrapper_params_CB_bound(PyObject *self, PyObject *args);
static PyObject *wrapper_params_CB_solve_a(PyObject *self, PyObject *args);
static PyObject *wrapper_params_compute_delta(PyObject *self, PyObject *args);
static PyObject *wrapper_params_compute_RHS(PyObject *self, PyObject *args);
static PyObject *wrapper_params_compute_binomial_prob(PyObject *self,
                                                      PyObject *args);
static PyObject *wrapper_params_search_x_star(PyObject *self, PyObject *args);

/*
 * Methods exported by this module
 */
static PyMethodDef params_methods[] = {
    {"new", wrapper_params_new, METH_VARARGS},
    {"bf_num_bytes", wrapper_params_bf_num_bytes, METH_VARARGS},
    {"delete", wrapper_params_delete, METH_VARARGS},
    {"total", wrapper_params_total, METH_VARARGS},
    {"solve_a", wrapper_params_solve_a, METH_VARARGS},
    {"CB_bound", wrapper_params_CB_bound, METH_VARARGS},
    {"CB_solve_a", wrapper_params_CB_solve_a, METH_VARARGS},
    {"compute_delta", wrapper_params_compute_delta, METH_VARARGS},
    {"compute_RHS", wrapper_params_compute_RHS, METH_VARARGS},
    {"compute_binomial_prob", wrapper_params_compute_binomial_prob,
     METH_VARARGS},
    {"search_x_star", wrapper_params_search_x_star, METH_VARARGS},
    {NULL, NULL} /* Sentinel */
};

static PyObject *wrapper_params_new(PyObject *self, PyObject *args) {

  if (!PyArg_ParseTuple(args, ""))
    Py_RETURN_NONE;

  search_params *params_ptr = new search_params();
  return Py_BuildValue("l", params_ptr);
}

static PyObject *wrapper_params_delete(PyObject *self, PyObject *args) {
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "l", &params_ptr))
    Py_RETURN_NONE;

  delete params_ptr;

  return Py_BuildValue("");
}

static PyObject *wrapper_params_bf_num_bytes(PyObject *self, PyObject *args) {
  double error_rate;
  int capacity;
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "ldi", &params_ptr, &error_rate, &capacity))
    ;

  double num_bytes = params_ptr->bf_num_bytes(error_rate, capacity);

  return Py_BuildValue("d", num_bytes);
}

static PyObject *wrapper_params_total(PyObject *self, PyObject *args) {
  search_params *params_ptr;
  double a, fpr;
  int n, y, rows;
  if (!PyArg_ParseTuple(args, "lddii", &params_ptr, &a, &fpr, &n, &y))
    Py_RETURN_NONE;

  double tot = params_ptr->total(a, fpr, n, y, rows);

  return Py_BuildValue("di", tot, rows);
}

static PyObject *wrapper_params_solve_a(PyObject *self, PyObject *args) {
  // int m, int n, int x, int y, double &min_a, double &min_fpr, int
  // &min_iblt_rows
  int m, n, x, y, min_iblt_rows;
  double min_a, min_fpr;
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "liiii", &params_ptr, &m, &n, &x, &y))
    Py_RETURN_NONE;

  params_ptr->solve_a(m, n, x, y, min_a, min_fpr, min_iblt_rows);

  return Py_BuildValue("ddi", min_a, min_fpr, min_iblt_rows);
}

static PyObject *wrapper_params_CB_bound(PyObject *self, PyObject *args) {
  double a, fpr, bound;
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "lddd", &params_ptr, &a, &fpr, &bound))
    Py_RETURN_NONE;

  double ret = params_ptr->CB_bound(a, fpr, bound);

  return Py_BuildValue("d", ret);
}

static PyObject *wrapper_params_CB_solve_a(PyObject *self, PyObject *args) {
  int m, n, x, y, min_iblt_rows;
  double bound, min_a, min_fpr;
  search_params *params_ptr;

  if (!PyArg_ParseTuple(args, "liiiid", &params_ptr, &m, &n, &x, &y, &bound))
    Py_RETURN_NONE;

  params_ptr->CB_solve_a(m, n, x, y, bound, min_a, min_fpr, min_iblt_rows);

  return Py_BuildValue("ddi", min_a, min_fpr, min_iblt_rows);
}

static PyObject *wrapper_params_compute_delta(PyObject *self, PyObject *args) {
  int z, x, m;
  double fpr;
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "liiid", &params_ptr, &z, &x, &m, &fpr))
    Py_RETURN_NONE;

  double ret = params_ptr->compute_delta(z, x, m, fpr);
  return Py_BuildValue("d", ret);
}

static PyObject *wrapper_params_compute_RHS(PyObject *self, PyObject *args) {
  double delta, fpr;
  int m, x;
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "ldiid", &params_ptr, &delta, &m, &x, &fpr))
    Py_RETURN_NONE;

  double ret = params_ptr->compute_RHS(delta, m, x, fpr);
  return Py_BuildValue("d", ret);
}

static PyObject *wrapper_params_compute_binomial_prob(PyObject *self,
                                                      PyObject *args) {
  int z, x, m;
  double fpr;
  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "liiid", &params_ptr, &m, &x, &z, &fpr))
    Py_RETURN_NONE;

  double ret = params_ptr->compute_binomial_prob(m, x, z, fpr);
  return Py_BuildValue("d", ret);
}

static PyObject *wrapper_params_search_x_star(PyObject *self, PyObject *args) {
  int z, mempool_size;
  double fpr, bound;
  int blk_size;

  search_params *params_ptr;
  if (!PyArg_ParseTuple(args, "liiddi", &params_ptr, &z, &mempool_size, &fpr,
                        &bound, &blk_size))
    Py_RETURN_NONE;

  int ret = params_ptr->search_x_star(z, mempool_size, fpr, bound, blk_size);

  return Py_BuildValue("i", ret);
}

#if PY_MAJOR_VERSION >= 3
/* ! the struct name must respect the format: <name of the module> followed by
 * string "module"*/
static struct PyModuleDef paramsmodule = {
    PyModuleDef_HEAD_INIT, "params", /* name of module */
    NULL,                            /* module documentation, may be NULL */
    -1, /* size of per-interpreter state of the module,
           or -1 if the module keeps state in global variables. */
    params_methods};
#endif

/*
 * Module initialization
 */
#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit_params(void)
#else
PyMODINIT_FUNC initparams(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
  return PyModule_Create(&paramsmodule);
#else
  (void)Py_InitModule("params", params_methods);
#endif
}