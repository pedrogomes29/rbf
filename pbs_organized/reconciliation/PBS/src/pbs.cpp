#include <getopt.h>
#include <minisketch.h>
#include <xxhash.h>
#include <chrono>
#include <cassert>
#include <cmath>
#include <cstdlib> /* for exit */
#include <cstring>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <dirent.h>
#include <stdio.h>
#include "FileReader.h"
#include "SimpleTimer.h"
#include "random.h"

using namespace std;


#define INF_RATIO 1.38
#define SEED 42
#define AVG_DIFF 5
#define MAX_ROUND 3
#define SPLIT_NUM 3
#define SIGNATURE_WIDTH 64
#define CHECKSUM_LENGTH 32

// a wrapper for xxhash
uint myhash(uint64_t key, uint seed) { return XXH32(&key, sizeof(key), seed); }

// parity encoding v2
void Encode(const vector<uint64_t> &set,  // elements in a set
            vector<uint> &bit,        // parity bits after encoding
            vector<uint> &loc,        // hash value of each element
            vector<uint64_t> &elm_xor,    // xor of each bin
            uint seed                 // hash seed
) {
  size_t len = set.size();
  size_t n = bit.size();
  std::fill(bit.begin(), bit.end(), 0);
  std::fill(elm_xor.begin(), elm_xor.end(), 0);\

  for (size_t i = 0; i < len; ++i) {
    // make sure no one goes into the bin with id 0
    // since minisketch does not support it right now
    loc[i] = (myhash(set[i], seed) % (n - 1)) + 1;
    bit[loc[i]] ^= 1u;
    elm_xor[loc[i]] ^= set[i];
  }
}

struct Metric {
  // communication
  vector<std::size_t> com_bch_encoding;  // sketch sizes
  vector<std::size_t> com_bch_decoding;  // header plus bin indices
  vector<std::size_t>
      com_bch_decoding_verify;       // header plus "index" for exception I & II
  vector<std::size_t> com_xor;       // xor of decoded bins
  vector<std::size_t> com_checksum;  // checksum

  // computation
  vector<std::chrono::nanoseconds> t_decoding;
  vector<std::chrono::nanoseconds> t_encoding;

  // general
  vector<std::size_t> g_bch_decoding_failure;
  vector<std::size_t> g_num_groups;
  vector<std::size_t> g_exception_I;
  vector<std::size_t> g_exception_II;
  vector<std::size_t> g_true_recon;
  vector<std::size_t> g_false_recon;

  void clear() {
    com_bch_encoding.clear();
    com_bch_decoding.clear();
    com_bch_decoding_verify.clear();
    com_xor.clear();
    com_checksum.clear();

    t_decoding.clear();
    t_encoding.clear();

    g_bch_decoding_failure.clear();
    g_num_groups.clear();
    g_exception_I.clear();
    g_exception_II.clear();
    g_true_recon.clear();
    g_false_recon.clear();
  }

  double total_bytes(size_t i) const {
    auto total_bits =
        (double)(com_bch_decoding[i] + com_bch_encoding[i] +
                 com_bch_decoding_verify[i] + com_xor[i] + com_checksum[i]);
    return total_bits / 8.0;
  }

  static const char *header() {
    return "#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,"
           "truerec,falserec,paritybits,"
           "xornum,checksumbits,decodebits,checkbits,logn,t,assumed_diff_size,"
           "bch_failure,num_groups,failure_exception_I,failure_execption_II";
  }

  static const char *fmt() {
    return "%u,%u,%.2f,%d,%.8f,%.8f,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%"
           "u\n";
  }
};

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

// Hashing function to convert strings to 4-byte hashes (uint32_t).
std::unordered_map<uint64_t, string> hash_strings(const std::vector<std::string>& strings) {
    static_assert(sizeof(size_t) >= 8,
                "std hash returns size_t, assuming it's a 64 bit architecture");    
    std::unordered_map<uint64_t, string> hashes_to_strings;
    hashes_to_strings.reserve(strings.size());
    std::hash<std::string> hasher;
    for (const auto& s : strings) {
        hashes_to_strings.insert({static_cast<uint64_t>(hasher(s)), s});
    }
    return hashes_to_strings;
}

bool are_same_elements(const std::vector<std::string>& vec1, const std::vector<std::string>& vec2) {
    // If the sizes are different, they can't contain the same elements
    if (vec1.size() != vec2.size()) {
        return false;
    }

    // Insert all elements from the first vector into a hash set
    std::unordered_set<std::string> set1(vec1.begin(), vec1.end());

    // Check if every element from the second vector exists in the hash set
    for (const auto& element : vec2) {
        if (set1.find(element) == set1.end()) {
            return false; // Element not found, vectors are not the same
        }
    }

    // All elements were found, so the vectors contain the same elements
    return true;
}

// C++11 compatible function to get subdirectories
std::vector<std::string> get_subdirectories(const std::string& path) {
    std::vector<std::string> subdirs;
    DIR* dir = opendir(path.c_str());
    if (dir == NULL) {
        // Handle error, e.g., print a message
        std::cerr << "Could not open directory: " << path << std::endl;
        return subdirs;
    }
    struct dirent* entry;
    while ((entry = readdir(dir)) != NULL) {
        std::string name = entry->d_name;
        // Ignore . and .. directories
        if (name != "." && name != "..") {
            // Check if it's a directory
            // This is a simple heuristic, a more robust check would use stat()
            subdirs.push_back(name);
        }
    }
    closedir(dir);
    return subdirs;
}


std::pair<std::vector<uint64_t>, std::pair<int,Metric>> PBS(std::vector<uint64_t> setA, std::vector<uint64_t> setB, size_t diff_size, size_t logn, size_t t){
    size_t n = (1u << logn) - 1u;
    const size_t decode_header_len = ceil(log2(t + 2));
    const size_t sketch_each_len = logn * t;
    SimpleTimer timer;
    std::chrono::nanoseconds t_partition = std::chrono::nanoseconds(0);

    // partition
    timer.restart();
    // number of groups that are to be reconciled
    size_t remaining_num_groups =
      ceil(static_cast<float>(diff_size) / AVG_DIFF);
    size_t initial_num_groups = remaining_num_groups;
    vector<vector<uint64_t>> subA(remaining_num_groups);
    vector<vector<uint64_t>> subB(remaining_num_groups);
    vector<vector<uint64_t>> xorA, xorB;
    vector<size_t> group_id(remaining_num_groups);
    vector<uint64_t> reconciled;
    // partitioning
    for (size_t j = 0; j < setA.size(); ++j) {
      size_t index =
          myhash(setA[j], SEED) % remaining_num_groups;
      subA[index].push_back(setA[j]);
    }
    for (size_t j = 0; j < setB.size(); ++j) {
      size_t index =
          myhash(setB[j], SEED) % remaining_num_groups;
      subB[index].push_back(setB[j]);
    }
    // recording group id
    for (size_t j = 0; j < remaining_num_groups; ++j) {
      group_id[j] = j;
    }
    t_partition += timer.elapsed();

    /** Message Header Format in PBS
     *  0                                ceil(log2(t + 2))
     *  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     *  +  message header for each group  +
     *  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     *
     *  As shown above, for each group, we use $\lceil\log_2(t+2)\rceil$ bits
     * longer header to tell how many elements were decoded with BCH, where t is
     * the BCH decoding capacity. More precisely, a header value of $x \in
     * \{0,1,2,...,t\} means, there are x elements decoded, whereas a value of
     * $t+1$ (or -1) means decoding failed. Therefore, we need at most
     * $\lceil\log_2(t+2)\rceil$ bits for each group.
     *
     *  Followed by this header are the data field, which contains the indices
     * of the corresponding x (assuming the header value is $x \in
     * \{0,1,2,...,t\}) bins in this group, each of which takes $\log_2 n$ bits.
     * Then, the x+1 XORs, each of the first x XORs is the bitwise XOR for all
     * elements located in the corresponding bin, and the last one is a checksum
     * for the entire group.
     *
     *  Note that if BCH decoding failed, then a packet with only the header
     * message will be sent.
     *
     *  Since PBS allows multiple rounds, the host, upond receiving this packet,
     * should verify that result. If it finds that there are some remaining
     * un-reconciled elements, it should send a message to tell the other host.
     * In this implementation, we assume the following message format is used.
     *
     *  The 1st bit tells whether exception I (even number of distinct elements
     * partitining into the same bin) was detected, since in such a case, we
     * DONOT know which bin is. So, we should reconcile all elements in the bins
     * which do not belong to the x decoded bins. Then, we should use \lceil
     * \log_2 (x + 1) \rceil bits to tell whether exception II happens in the x
     * decoded bins.
     *
     * */

    int num_running_rounds = 1;

    Metric metric;
    metric.clear();



    while (remaining_num_groups > 0) {
      // initialize metric's member variables
      metric.com_bch_encoding.push_back(remaining_num_groups * sketch_each_len);
      metric.com_checksum.push_back(remaining_num_groups *
                                    CHECKSUM_LENGTH);
      metric.com_bch_decoding.push_back(remaining_num_groups *
                                        decode_header_len);
      metric.com_xor.push_back(0);
      metric.com_bch_decoding_verify.push_back(0);

      metric.t_decoding.push_back(std::chrono::nanoseconds(0));
      metric.t_encoding.push_back(t_partition);

      metric.g_bch_decoding_failure.push_back(0);
      metric.g_exception_I.push_back(0);
      metric.g_exception_II.push_back(0);
      metric.g_num_groups.push_back(remaining_num_groups);
      metric.g_true_recon.push_back(0);
      metric.g_false_recon.push_back(0);

      vector<size_t> failed_subsets;
      xorA.resize(remaining_num_groups);
      xorB.resize(remaining_num_groups);

      std::chrono::nanoseconds dummy_patition_time = std::chrono::nanoseconds(0);  // for addressing exception I & II

      for (size_t j = 0; j < remaining_num_groups; ++j) {
        timer.restart();
        xorA[j].resize(n);
        xorB[j].resize(n);
        size_t subset_a_size = subA[j].size();
        size_t subset_b_size = subB[j].size();
        vector<uint> bitA(n);
        vector<uint> bitB(n);
        vector<uint> locA(subset_a_size);
        vector<uint> locB(subset_b_size);
        // partition into groups
        Encode(subA[j], bitA, locA, xorA[j],
              SEED + num_running_rounds);
        Encode(subB[j], bitB, locB, xorB[j],
              SEED + num_running_rounds);
        metric.t_encoding.back() += timer.elapsed();

        // BCH encoding
        timer.restart();
        minisketch *sketch_a = minisketch_create(logn, 0, t);
        minisketch *sketch_b = minisketch_create(logn, 0, t);
        for (size_t k = 0; k < n; ++k) {
          if (bitA[k]) minisketch_add_uint64(sketch_a, k);
        }
        for (size_t k = 0; k < n; ++k) {
          if (bitB[k]) minisketch_add_uint64(sketch_b, k);
        }
        metric.t_encoding.back() += timer.elapsed();

        // BCH decoding
        timer.restart();
        vector<uint64_t> pos(t);
        minisketch_merge(sketch_b, sketch_a);
        int p = minisketch_decode(sketch_b, t, &pos[0]);
        minisketch_destroy(sketch_a);
        minisketch_destroy(sketch_b);
        metric.t_decoding.back() += timer.elapsed();

        if (p >= 0) {  // decoding succeeded
          {
            // do measurement
            metric.com_xor.back() += p * SIGNATURE_WIDTH;
            metric.com_bch_decoding.back() += p * logn;
            // one bit for indicating exception I, the rest for indicating
            // whether there is exception II
            metric.com_bch_decoding_verify.back() += ceil(log2(p + 1)) + 1;
          }

          // calculate XORs
          timer.restart();
          // ???: changed from (t+1) => (p+1)
          vector<uint64_t> XOR(p + 1, 0);
          vector<uint> ind(n, 0);

          for (int k = 0; k < p; ++k) {
            ind[pos[k]] = k + 1;
          }
          for (size_t bi = 1; bi < n; ++bi) {
            XOR[ind[bi]] ^= (xorA[j][bi] ^ xorB[j][bi]);
          }
          metric.t_decoding.back() += timer.elapsed();

          std::vector<int> exception_II_groups;

          // xor decoding
          timer.restart();
          if (XOR[0] != 0) metric.g_exception_I.back()++;
          for (int k = 1; k <= p; ++k) {
            if (XOR[k]) {// odd number of distinct elements
              if (myhash(XOR[k], SEED + num_running_rounds) %
                              (n - 1) +
                          1 ==
                      pos[k - 1] &&
                  myhash(XOR[k], SEED) % initial_num_groups ==
                      (unsigned)group_id[j]) {
                reconciled.push_back(XOR[k]);
              } else {
                metric.g_exception_II.back()++;
                exception_II_groups.push_back(k);
              }
            }
          }
          metric.t_decoding.back() += timer.elapsed();  // time to decode xor

          timer.restart();
          // The XORs of all the elements in the buckets whose
          // does not contain any balls should be zero!
          // If it is not ===> collision happens (even number of balls go into
          // the same bin)
          if (XOR[0] != 0) {
            size_t old_size = subA.size();
            subA.resize(old_size + 1);
            subB.resize(old_size + 1);
            group_id.resize(old_size + 1);
            for (size_t k = 0; k < subset_a_size; ++k) {
              if (!ind[locA[k]]) {
                subA[old_size].push_back(subA[j][k]);
              }
            }
            for (size_t k = 0; k < subset_b_size; ++k) {
              if (!ind[locB[k]]) {
                subB[old_size].push_back(subB[j][k]);
              }
            }
            group_id[old_size] = group_id[j];
          }

          // for (int k = 1; k <= p; ++k) {
          //   if (XOR[k]) {
          //     if (myhash(XOR[k], pbs_params.seeds[i] + num_running_rounds) %
          //                     (n - 1) +
          //                 1 ==
          //             pos[k - 1] &&
          //         myhash(XOR[k], pbs_params.seeds[i]) % initial_num_groups ==
          //             (unsigned)group_id[j]) {
          //       reconciled.push_back(XOR[k]);
          //       if (diff.count(XOR[k]))
          //         metric.g_true_recon.back()++;
          //       else
          //         metric.g_false_recon.back()++;
          //     } else {
          //       metric.g_exception_II.back()++;
          //       // here, we can actually save some space, for example, we
          //       // can use use log_2 p bits. However, this event happens
          //       // rarely, this saving is negligible.
          //       metric.com_bch_decoding_verify.back() += logn;
          //       size_t old_size = subA.size();
          //       subA.resize(old_size + 1);
          //       subB.resize(old_size + 1);
          //       group_id.resize(old_size + 1);
          //       for (size_t q = 0; q < subset_a_size; ++q) {
          //         if (locA[q] == pos[k - 1]) {
          //           subA[old_size].push_back(subA[j][q]);
          //         }
          //       }
          //       for (size_t q = 0; q < subset_b_size; ++q) {
          //         if (locB[q] == pos[k - 1]) {
          //           subB[old_size].push_back(subB[j][q]);
          //         }
          //       }
          //       group_id[old_size] = group_id[j];
          //     }
          //   }
          // }
          for (int k : exception_II_groups) {
            // if (XOR[k]) {
            //   if (myhash(XOR[k], pbs_params.seeds[i] + num_running_rounds) %
            //                   (n - 1) +
            //               1 ==
            //           pos[k - 1] &&
            //       myhash(XOR[k], pbs_params.seeds[i]) % initial_num_groups ==
            //           (unsigned)group_id[j]) {
            //     reconciled.push_back(XOR[k]);
            //     if (diff.count(XOR[k]))
            //       metric.g_true_recon.back()++;
            //     else
            //       metric.g_false_recon.back()++;
            //   } else {
            //     metric.g_exception_II.back()++;
            // here, we can actually save some space, for example, we
            // can use use log_2 p bits. However, this event happens
            // rarely, this saving is negligible.
            metric.com_bch_decoding_verify.back() += logn;
            size_t old_size = subA.size();
            subA.resize(old_size + 1);
            subB.resize(old_size + 1);
            group_id.resize(old_size + 1);
            for (size_t q = 0; q < subset_a_size; ++q) {
              if (locA[q] == pos[k - 1]) {
                subA[old_size].push_back(subA[j][q]);
              }
            }
            for (size_t q = 0; q < subset_b_size; ++q) {
              if (locB[q] == pos[k - 1]) {
                subB[old_size].push_back(subB[j][q]);
              }
            }
            group_id[old_size] = group_id[j];
          }
          //   }
          // }
          dummy_patition_time += timer.elapsed();  // time to decode xor

        } else {  // p = -1, failed to decode
          failed_subsets.push_back(j);
          metric.g_bch_decoding_failure.back()++;
        }
      }
      
      t_partition = dummy_patition_time;  //
      // address bch decoding failure exception
      if (!failed_subsets.empty()) {
        timer.restart();
        for (auto j : failed_subsets) {
          size_t old_size = subA.size();
          size_t subset_a_size = subA[j].size();
          size_t subset_b_size = subB[j].size();
          subA.resize(old_size + SPLIT_NUM);
          subB.resize(old_size + SPLIT_NUM);
          group_id.resize(old_size + SPLIT_NUM);
          for (size_t k = 0; k < subset_a_size; ++k) {
            size_t index =  
                myhash(subA[j][k], SEED + num_running_rounds) %
                SPLIT_NUM;
            subA[old_size + index].push_back(subA[j][k]);
          }
          for (size_t k = 0; k < subset_b_size; ++k) {
            size_t index =
                myhash(subB[j][k], SEED + num_running_rounds) %
                SPLIT_NUM;
            subB[old_size + index].push_back(subB[j][k]);
          }
          for (size_t k = 0; k < SPLIT_NUM; ++k) {
            group_id[old_size + k] = group_id[j];
          }
        }
        t_partition += timer.elapsed();
      }
      // update number of groups
      subA.erase(subA.begin(), subA.begin() + remaining_num_groups);
      subB.erase(subB.begin(), subB.begin() + remaining_num_groups);
      group_id.erase(group_id.begin(), group_id.begin() + remaining_num_groups);
      remaining_num_groups = subA.size();

      //
      xorA.clear();
      xorB.clear();
      ++num_running_rounds;
    }

    return {reconciled, {num_running_rounds, metric}};
}



int main(int argc, char **argv) {

  if (argc != 4) {
    std::cerr << "Usage: " << argv[0] << " <input_dir> <nr_tests> <output_dir>" << std::endl;
    return 1; // Return a non-zero value to indicate an error
  }
  std::string input_dir = argv[1];
  size_t nr_tests = (size_t) stoi(argv[2]);
  std::string output_dir = argv[3];

  auto algo_path = output_dir + "/PBS.csv";
  FILE* ofp = fopen(algo_path.c_str(), "w");

  
  // Dynamically find 'd_' directories instead of hard-coding them.
  std::vector<std::string> d_dirs;
  for (const auto& entry_name : get_subdirectories(input_dir)) {
      if (entry_name.rfind("d_", 0) == 0) {
          d_dirs.push_back(entry_name);
      }
  }

  int i=0;
  SimpleTimer timer;
  // Iterate through 'd' directories
  for (const auto& d_dir_name : d_dirs) {
      std::string d_str = d_dir_name.substr(2); // Remove "d_"
      size_t d = std::stoul(d_str);
      std::string current_d_path = input_dir + "/" + d_dir_name;
      cout << "Running tests with d=" << d << " index="<< i++ <<"\n";
      timer.restart();
      for(size_t test_nr=0; test_nr<nr_tests; test_nr++){
          SimpleTimer timer;
          size_t state = 0;
          size_t metadata = 0;
          std::chrono::nanoseconds t_enc = std::chrono::nanoseconds(0);
          std::chrono::nanoseconds t_dec = std::chrono::nanoseconds(0);

          std::stringstream ss;

          ss << current_d_path << "/" << "test_" << test_nr;
          std::string current_test_path = ss.str();
          std::string common_path = current_test_path + "/" + "common";
          std::string local_only_path = current_test_path + "/" + "local_only";
          std::string remote_only_path = current_test_path + "/" + "remote_only";

          // Read the sets from files
          std::vector<std::string> common_strings = read_file_to_vec(common_path);
          std::vector<std::string> local_only_strings = read_file_to_vec(local_only_path);
          std::vector<std::string> remote_only_strings = read_file_to_vec(remote_only_path);

          // Combine and hash the strings
          std::vector<std::string> local;
          local.insert(local.end(), common_strings.begin(), common_strings.end());
          local.insert(local.end(), local_only_strings.begin(), local_only_strings.end());

          std::vector<std::string> remote;
          remote.insert(remote.end(), common_strings.begin(), common_strings.end());
          remote.insert(remote.end(), remote_only_strings.begin(), remote_only_strings.end());
          

          timer.restart();
          std::unordered_map<uint64_t, string> local_hashes_to_elems = hash_strings(local);
          std::unordered_map<uint64_t, string> remote_hashes_to_elems = hash_strings(remote);
          //time to encode elements as digests
          t_enc += timer.elapsed();

          std::vector<uint64_t> local_hashes;
          local_hashes.reserve(local_hashes_to_elems.size());
          for(auto [local_hash, local_elem]: local_hashes_to_elems){
            local_hashes.push_back(local_hash);
          }

          std::vector<uint64_t> remote_hashes;
          remote_hashes.reserve(remote_hashes_to_elems.size());
          for(auto [remote_hash, remote_elem]: remote_hashes_to_elems){
            remote_hashes.push_back(remote_hash);
          }


          std::string tow_estimate_path = current_test_path + "/" + "tow_estimate.txt";
          std::ifstream tow_estimate_file(tow_estimate_path);
          double diff_size;
          if (tow_estimate_file.is_open()) {
              tow_estimate_file >> diff_size;
          } else {
              std::cerr << "Failed to open tow_estimate.txt: " << tow_estimate_path << std::endl;
          }

          vector<uint64_t> differing_hashes;
          Metric metric;
          int num_running_rounds = 0;

          if(std::abs(diff_size - 0.0) > std::numeric_limits<double>::epsilon()){ 
            //nr_diff is not 0
            std::string params_path = current_test_path + "/" + "params.txt";

            // Read the n and t values from params.txt
            std::ifstream params_file(params_path);
            size_t logn, t;
            double first_val;
            if (params_file.is_open()) {
                params_file >> first_val >> logn >> t;
            } else {
                std::cerr << "Failed to open params.txt: " << params_path << std::endl;
            }
            size_t scaled_diff_size = size_t(ceil(diff_size * INF_RATIO));
            auto pbs_result = PBS(local_hashes, remote_hashes, scaled_diff_size, logn, t);
            differing_hashes = pbs_result.first;
            auto metric_result = pbs_result.second;
            num_running_rounds = metric_result.first;
            metric = metric_result.second;
          }

          for (int j = 0; j < num_running_rounds - 1; ++j) {
            metadata += metric.total_bytes(j);
            t_enc += metric.t_encoding[j];
            t_dec += metric.t_decoding[j];
          }


          std::vector<uint64_t> local_only_hashes;
          std::vector<uint64_t> remote_only_hashes;
          timer.restart();
          for(uint64_t hash: differing_hashes){
            if(local_hashes_to_elems.find(hash) != local_hashes_to_elems.end()){
              local_only_hashes.push_back(hash);
            }else if(remote_hashes_to_elems.find(hash) != remote_hashes_to_elems.end()){
              remote_only_hashes.push_back(hash);
            }else{
              std::cerr << "Recovered hash is unknown\n";
            }
          }
          //time to partition hashes into local only and remote only 
          t_dec += timer.elapsed();


          timer.restart();
          std::vector<string> remote_only_elements;
          remote_only_elements.reserve(remote_only_hashes.size());
          for(uint64_t hash: remote_only_hashes){
            string elem = remote_hashes_to_elems[hash];
            remote_only_elements.push_back(elem);
          }
          //time to partition obtain remote only elements from hashes
          t_dec += timer.elapsed();


          for(string elem: remote_only_elements){
            state += elem.size();
          }
          for(uint64_t hash: local_only_hashes){
            metadata += sizeof(hash);
          }


          timer.restart();
          std::vector<string> local_only_elements;
          local_only_elements.reserve(local_only_hashes.size());
          for(uint64_t hash: local_only_hashes){
            string elem = local_hashes_to_elems[hash];
            local_only_elements.push_back(elem);
          }
          //time to partition obtain local only elements from hashes
          t_dec += timer.elapsed();

          for(string elem: local_only_elements){
            state += elem.size();
          }

          // 9. Sanity Check
          local.insert(local.end(), remote_only_elements.begin(), remote_only_elements.end());
          remote.insert(remote.end(), local_only_elements.begin(), local_only_elements.end());

          if (!are_same_elements(local, remote)) {
              std::cerr << "Reconciliation failed: local and remote vectors do not match." << std::endl;
              exit(EXIT_FAILURE);
          }

          fprintf(ofp, "%ld,%ld,%ld,%ld,%ld\n", d, state, metadata, t_enc.count(), t_dec.count());
      }  
      cout << "Took: " << timer.elapsed().count()/1000000000 << "s\n";
  }





  fclose(ofp);
  return 0;
}