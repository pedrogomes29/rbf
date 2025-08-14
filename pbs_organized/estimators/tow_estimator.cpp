#include <getopt.h>

#include <cstdlib>
#include <cstring>
#include <iomanip>

#include "FileReader.h"
#include "tow.h"
#include "xxhash_wrapper.h"
#include <iostream>

#include <dirent.h>
#include <stdio.h>


int NUM_SKETCH = 128;
unsigned SEED = 42;
int KEY_BITS = 64;


#ifdef DEBUG
#define debug(...) fprintf(stdout, __VA_ARGS__)
#else
#define debug(...)
#endif


// Function to read a file into a vector of strings.
std::vector<std::string> read_file_to_vec(const std::string& path) {
    std::vector<std::string> lines;
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + path);
    }
    std::string line;
    while (std::getline(file, line)) {
        lines.push_back(line);
    }
    return lines;
}

std::vector<uint32_t> hash_strings(const std::vector<std::string>& strings) {
    std::vector<uint32_t> hashes;
    hashes.reserve(strings.size());
    std::hash<std::string> hasher;
    for (const auto& s : strings) {
        hashes.push_back(static_cast<uint32_t>(hasher(s)));
    }
    return hashes;
}



template <typename KEY_TYPE>
double ToW32(const std::vector<KEY_TYPE> &setA,
             const std::vector<KEY_TYPE> &setB, int num_sketches,
             unsigned seed) {
  static_assert(sizeof(KEY_TYPE) <= 4,
                "ToW32 only support key types with less than 32 bits");
  TugOfWarHash<XXHash> tow(num_sketches, seed);

  auto sketchA = tow.template apply<KEY_TYPE>(setA);
  auto sketchB = tow.template apply<KEY_TYPE>(setB);

  double d = 0.0, tmp;

  for (size_t i = 0; i < sketchA.size(); ++i) {
    tmp = sketchA[i] - sketchB[i];
    d += tmp * tmp;
  }

  return d / num_sketches;
}




int main(int argc, char *argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_directory>" << std::endl;
        return 1;
    }
    std::string test_path = argv[1];
    std::string common_path = test_path + "/" + "common";
    std::string local_only_path = test_path + "/" + "local_only";
    std::string remote_only_path = test_path + "/" + "remote_only";

    // Read the sets from files
    std::vector<std::string> common_strings = read_file_to_vec(common_path);
    std::vector<std::string> local_only_strings = read_file_to_vec(local_only_path);
    std::vector<std::string> remote_only_strings = read_file_to_vec(remote_only_path);

    // Combine and hash the strings
    std::vector<std::string> local_all_strings;
    local_all_strings.insert(local_all_strings.end(), common_strings.begin(), common_strings.end());
    local_all_strings.insert(local_all_strings.end(), local_only_strings.begin(), local_only_strings.end());

    std::vector<std::string> remote_all_strings;
    remote_all_strings.insert(remote_all_strings.end(), common_strings.begin(), common_strings.end());
    remote_all_strings.insert(remote_all_strings.end(), remote_only_strings.begin(), remote_only_strings.end());

    std::vector<uint32_t> local_hashes = hash_strings(local_all_strings);
    std::vector<uint32_t> remote_hashes = hash_strings(remote_all_strings);

    // Run the Tow estimator
    const int NUM_SKETCH = 128;
    const unsigned SEED = 42;
    auto tow_estimate = ToW32<uint32_t>(local_hashes, remote_hashes, NUM_SKETCH, SEED);

    // Write the estimate to a file
    std::string tow_path = test_path + "/" + "tow_estimate.txt";
    std::ofstream tow_file(tow_path);
    if (tow_file.is_open()) {
        tow_file << tow_estimate;
    } else {
        std::cerr << "Failed to write to " << tow_path << std::endl;
    }
}
