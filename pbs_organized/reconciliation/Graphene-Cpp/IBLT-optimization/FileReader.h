#ifndef __FILE_READER_H__
#define __FILE_READER_H__

#include <fstream>
#include <string>
#include <vector>

class TxTFileReader {
public:
  explicit TxTFileReader(std::string filename)
      : _filename(std::move(filename)) {
    inf.open(_filename, std::ios::in);
    if (!inf.is_open()) {
      throw std::runtime_error("Failed to read file: " + _filename);
    }
  }

  void skip_lines(size_t n = 1) {
    std::string skipped;
    int line = 0;
    while (!inf.eof() && line < n) {
      getline(inf, skipped);
      ++line;
    }
  }

  template <typename num_t> size_t read(std::vector<num_t> &data, size_t n) {
    data.resize(n);
    size_t size = read<num_t>(&data[0], n);
    data.resize(size);
    return size;
  }

  template <typename num_t> size_t read(num_t *data, size_t n) {
    size_t size = read<num_t>(data, n, inf);
    return size;
  }

  template <typename num_t> void read(num_t **data, size_t m, size_t n) {
    for (size_t r = 0; r < m; r++) {
      if (read<num_t>(data[r], n, inf) != n) {
        throw std::runtime_error("Dimension mismatch");
      }
    }
  }

  template <typename num_t>
  void read(std::vector<std::vector<num_t>> &data, size_t m, size_t n) {
    if (data.size() != m) {
      data.resize(m);
    }
    for (size_t r = 0; r < m; r++) {
      if (data[r].size() != n) {
        data[r].resize(n);
      }
      if (read<num_t>(&data[r][0], n, inf) != n) {
        throw std::runtime_error("Dimension mismatch");
      }
    }
  }

  ~TxTFileReader() {
    if (inf.is_open()) {
      inf.close();
    }
  }

private:
  template <typename num_t>
  size_t read(num_t *data, size_t n, std::istream &inf) {
    int size = 0;
    while (!inf.eof() && size < n) {
      inf >> data[size++];
    }
    return size;
  }

  template <typename num_t>
  void write(const num_t *data, size_t n, std::ostream &os) {
    if (n == 0)
      return;
    int size = 0;
    while (size < n - 1) {
      os << data[size++] << " ";
    }
    os << data[size];
  }

  std::string _filename;
  std::ifstream inf;
};

#endif // __FILE_READER_H__