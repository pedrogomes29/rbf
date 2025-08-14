#ifndef __TOW_H__
#define __TOW_H__

#include <cassert>
#include <climits>
#include <cstdio>
#include <random>
#include <unordered_map>
#include <unordered_set>

template <typename MyHash>
struct TugOfWarHash {
  TugOfWarHash(size_t m, unsigned seed, uint64_t max_range = UINT_MAX)
      : seed_(seed), m_(m), max_range_(max_range), hash_{} {
    generate_hashes();
  }

  template <typename ElementType = uint32_t>
  int apply(const std::vector<ElementType> &data, size_t index) {
    assert(index < m_);
    int res = 0;
    for (auto v : data) {
      res += (hash_[index](v) % 2 == 0) ? (-1) : (+1);
    }
    return res;
  }

  template <typename ElementType = uint32_t>
  std::vector<int> apply(const std::vector<ElementType> &data) {
    std::vector<int> sketches(m_, 0);
    for (size_t i = 0; i < m_; ++i) {
      sketches[i] = apply<ElementType>(data, i);
    }
    return sketches;
  }

 private:
  void generate_hashes() {
    hash_.reserve(m_);
    std::mt19937_64 eg(seed_);
    std::uniform_int_distribution<> uniform(0, max_range_);
    std::unordered_set<unsigned> hash_seeds;
    hash_seeds.reserve(m_);
    while (hash_seeds.size() < m_) {
      hash_seeds.insert(uniform(eg));
    }
    for (auto seed : hash_seeds) {
      // debug("Creating hash function %llu with seed %u\n", hash_.size() + 1,
      //       seed);
      hash_.emplace_back(seed);
    }
  }

  unsigned seed_;
  size_t m_;  // #
  uint64_t max_range_;
  std::vector<MyHash> hash_;
};
#endif  // __TOW_H__
