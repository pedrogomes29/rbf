#include <iostream>
#include <string>

#include "bloom_filter.hpp"
#include <cassert>
#include <cstdio>

void test_int_type(size_t num_inserted = 100000, double fpr = 0.01) {
  printf("Test for int type with %lu insertions and a fpr of %.4lf...\n",
         num_inserted, fpr);
  bloom_parameters parameters;

  // How many elements roughly do we expect to insert?
  parameters.projected_element_count = num_inserted;

  // Maximum tolerable false positive probability? (0,1)
  parameters.false_positive_probability = fpr; // 1 in 100

  // Simple randomizer (optional)
  parameters.random_seed = 0xA5A5A5A5;

  if (!parameters) {
    std::cout << "Error - Invalid set of bloom filter parameters!" << std::endl;
    return;
  }

  parameters.compute_optimal_parameters();

  // Instantiate Bloom Filter
  bloom_filter filter(parameters);

  std::cout << "size: " << filter.size() << ", k: " << filter.hash_count()
            << std::endl;

  // std::cout << "sizeof(uint32_t) : " << sizeof(uint32_t) << std::endl;
  for (int i = 0; i < (int)num_inserted; ++i)
    filter.insert(i);

  // for (size_t i = 0; i < parameters.projected_element_count; ++i)
  //   assert(filter.contains(i));

  size_t cf = 0;
  size_t ct = 0;

  for (int i = (int)num_inserted; i < (int)num_inserted * 2; ++i) {
    if (filter.contains(i))
      cf++;
    ct++;
  }

  // Output the measured false positive rate
  std::cout << "false positive rate is " << 100.0 * cf / ct << "%\n";
}

void test_unsigned_int_type(size_t num_inserted = 100000, double fpr = 0.01) {
  printf(
      "Test for unsigned int type with %lu insertions and a fpr of %.4lf...\n",
      num_inserted, fpr);
  bloom_parameters parameters;

  // How many elements roughly do we expect to insert?
  parameters.projected_element_count = num_inserted;

  // Maximum tolerable false positive probability? (0,1)
  parameters.false_positive_probability = fpr; // 1 in 100

  // Simple randomizer (optional)
  parameters.random_seed = 0xA5A5A5A5;

  if (!parameters) {
    std::cout << "Error - Invalid set of bloom filter parameters!" << std::endl;
    return;
  }

  parameters.compute_optimal_parameters();

  // Instantiate Bloom Filter
  bloom_filter filter(parameters);

  std::cout << "size: " << filter.size() << ", k: " << filter.hash_count()
            << std::endl;

  for (unsigned i = 0; i < num_inserted; ++i)
    filter.insert(i);

  size_t cf = 0;
  size_t ct = 0;

  for (unsigned i = num_inserted; i < num_inserted * 2; ++i) {
    if (filter.contains(i))
      cf++;
    ct++;
  }

  // Output the measured false positive rate
  std::cout << "false positive rate is " << 100.0 * cf / ct << "%\n";
}

int main() {
  test_int_type();

  test_unsigned_int_type();
  return 0;
}