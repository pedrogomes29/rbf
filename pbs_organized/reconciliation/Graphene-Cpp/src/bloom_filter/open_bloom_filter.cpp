#include "bloom_filter.hpp"
#include <Python.h>

#include <bits/stdc++.h>

static PyObject *wrapper_obf_new(PyObject *self, PyObject *args);
static PyObject *wrapper_obf_delete(PyObject *self, PyObject *args);
static PyObject *wrapper_obf_add(PyObject *self, PyObject *args);
static PyObject *wrapper_obf_check(PyObject *self, PyObject *args);
static PyObject *wrapper_obf_num_hashes(PyObject *self, PyObject *args);
static PyObject *wrapper_obf_num_bits(PyObject *self, PyObject *args);

/*
 * Methods exported by this module
 */
static PyMethodDef obf_methods[] = {
    {"new", wrapper_obf_new, METH_VARARGS},
    {"delete", wrapper_obf_delete, METH_VARARGS},
    {"add", wrapper_obf_add, METH_VARARGS},
    {"check", wrapper_obf_check, METH_VARARGS},
    {"num_hashes", wrapper_obf_num_hashes, METH_VARARGS},
    {"num_bits", wrapper_obf_num_bits, METH_VARARGS},
    {NULL, NULL}};

static PyObject *wrapper_obf_new(PyObject *self, PyObject *args) {
  bloom_parameters parameters;
  bloom_filter *filter = nullptr;
  unsigned int est_entries;
  double fpr;
  unsigned int seed;

  if (!PyArg_ParseTuple(args, "IdI", &est_entries, &fpr, &seed))
    Py_RETURN_NONE;

  parameters.projected_element_count = est_entries;
  if (seed > 0)
    parameters.random_seed = seed;
  parameters.false_positive_probability = fpr;

  parameters.compute_optimal_parameters();
  filter = new bloom_filter(parameters);

  return Py_BuildValue("l", filter);
}

static PyObject *wrapper_obf_delete(PyObject *self, PyObject *args) {
  bloom_filter *filter = nullptr;

  if (!PyArg_ParseTuple(args, "l", &filter))
    Py_RETURN_NONE;

  delete filter;

  return Py_BuildValue("");
}

static PyObject *wrapper_obf_add(PyObject *self, PyObject *args) {
  bloom_filter *filter = nullptr;
  int key;
  if (!PyArg_ParseTuple(args, "li", &filter, &key))
    Py_RETURN_NONE;

  filter->insert(key);

  return Py_BuildValue("");
}

static PyObject *wrapper_obf_check(PyObject *self, PyObject *args) {
  bloom_filter *filter = nullptr;
  int key;
  if (!PyArg_ParseTuple(args, "li", &filter, &key))
    Py_RETURN_NONE;
  int res = 0;
  if (filter->contains(key))
    res = 1;
  return Py_BuildValue("i", res);
}

static PyObject *wrapper_obf_num_hashes(PyObject *self, PyObject *args) {
  bloom_filter *filter = nullptr;

  if (!PyArg_ParseTuple(args, "l", &filter))
    Py_RETURN_NONE;

  return Py_BuildValue("I", (unsigned)filter->hash_count());
}

static PyObject *wrapper_obf_num_bits(PyObject *self, PyObject *args) {
  bloom_filter *filter = nullptr;

  if (!PyArg_ParseTuple(args, "l", &filter))
    Py_RETURN_NONE;

  return Py_BuildValue("I", (unsigned)filter->size());
}

#if PY_MAJOR_VERSION >= 3
/* ! the struct name must respect the format: <name of the module> followed by
 * string "module"*/
static struct PyModuleDef obfmodule = {
    PyModuleDef_HEAD_INIT, "obf", /* name of module */
    NULL,                         /* module documentation, may be NULL */
    -1, /* size of per-interpreter state of the module,
           or -1 if the module keeps state in global variables. */
    obf_methods};
#endif

/*
 * Module initialization
 */
#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit_obf(void)
#else
PyMODINIT_FUNC initobf(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
  return PyModule_Create(&obfmodule);
#else
  (void)Py_InitModule("obf", obf_methods);
#endif
}