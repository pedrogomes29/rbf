#include "FileReader.h"
#include "SimpleTimer.h"
#include "iblt.h"
#include "utilstrencodings.h"
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <getopt.h>
#include <iomanip>
#include <iostream>
#include <unordered_set>
#include <vector>

using namespace std;

#define MAX_FILENAME_LEN 512

int N_TEST = 0;
int DIFF_SIZE = 0;
int DIFF_START = -1;
int UNION_SIZE = 0;
float EST_DIFF_SIZE = 0;
char ESTDIFFSIZE_FILE[MAX_FILENAME_LEN];
bool USE_EST = false;
float EST_INFLATION_RATIO = -1.0;
float HEDGE = 2.0; // use suggested value provided in what's difference paper

const int KEY_SIZE = 4; // bytes
const int VAL_SIZE = 1; // bytes
const int BYTES_EACH_CELL = 12;
int NUM_HASHES = 4;

#include <cmath>
#include <cstdio>
#ifdef DEBUG
#define debug(...) fprintf(stdout, __VA_ARGS__)
#else
#define debug(...)
#endif

void usage(const char *progname) {
  printf("Usage: %s -n NTEST -d DIFFSIZE -s DIFFSTART -u UNIONSIZE [-e "
         "ESTFILENAME -r ESTINFLATIONRATIO]\n",
         progname);
  exit(1);
}

void arg_parse(int argc, char *argv[]) {
  int c;
  char *progname;
  char *p;

  progname = ((p = strrchr(argv[0], '/')) ? ++p : argv[0]);

  memset(ESTDIFFSIZE_FILE, 0, MAX_FILENAME_LEN);
  while (true) {
    static struct option long_options[] = {
        {"ntest", required_argument, nullptr, 'n'},
        {"diffsize", required_argument, nullptr, 'd'},
        {"diffstart", required_argument, nullptr, 's'},
        {"unionsize", required_argument, nullptr, 'u'},
        //{"hedge", required_argument, nullptr, 'h'},
        {"estfilename", optional_argument, nullptr, 'e'},
        //{"estinflationratio", optional_argument, nullptr, 'r'},
        {nullptr, 0, nullptr, 0}};
    /* getopt_long stores the option index here. */
    int option_index = 0;

    c = getopt_long(argc, argv, "n:d:s:u:h:e:r:", long_options, &option_index);

    /* Detect the end of the options. */
    if (c == -1)
      break;

    switch (c) {
    case 'n':
      debug("option -n with value `%s'\n", optarg);
      N_TEST = atoi(optarg);
      break;

    case 'd':
      debug("option -d with value `%s'\n", optarg);
      DIFF_SIZE = atoi(optarg);
      break;

    case 's':
      debug("option -s with value `%s'\n", optarg);
      DIFF_START = atoi(optarg);
      break;

    case 'u':
      debug("option -u with value `%s'\n", optarg);
      UNION_SIZE = atoi(optarg);
      break;

    /*case 'h':
      debug("option -h with value `%s'\n", optarg);

      HEDGE = atof(optarg);

      break;*/

    case 'e':
      debug("option -e with value `%s'\n", optarg);

      strcpy(ESTDIFFSIZE_FILE, optarg);

      USE_EST = true;

      break;
   /* case 'r':
      debug("option -r with value `%s'\n", optarg);

      EST_INFLATION_RATIO = atof(optarg);

      break;*/

    case '?':
      usage(progname);

      break;

    default:
      usage(progname);
    }
  }

  /*

  if (EST_INFLATION_RATIO > 0) {
    assert(EST_INFLATION_RATIO >= 1.0);
    assert(USE_EST);
  }*/

  /*if (UNION_SIZE <= 0 || DIFF_SIZE <= 0 || N_TEST < 0 || DIFF_START == -1 ||
      HEDGE < 1.0) {
    usage(progname);
  }*/

    if (UNION_SIZE <= 0 || DIFF_SIZE <= 0 || N_TEST < 0 || DIFF_START == -1 ) {
    usage(progname);
  }
}

int main(int argc, char *argv[]) {
  arg_parse(argc, argv);

  ofstream fout;

  auto filename = to_string(UNION_SIZE) + "_" + to_string(DIFF_SIZE) + "_" +
                  to_string(USE_EST) + "_" + to_string(N_TEST) +
                  "_KeyDigest.txt";
  fout.open(filename);

  if (!fout.is_open()) {
    fprintf(stderr, "Failed to open %s\n", filename.c_str());
    exit(1);
  }

  fout << setw(15) << "ntest" << setw(15) << N_TEST << endl;
  fout << setw(15) << "unionsize" << setw(15) << UNION_SIZE << endl;
  fout << setw(15) << "diffsize" << setw(15) << DIFF_SIZE << endl;
  fout << setw(15) << "useest" << setw(15) << USE_EST << endl;
  fout << "# ====================================================\n";

  // TxTFileReader reader("../../test-sets/sets_100000_1000_32_1574465740.txt");
  TxTFileReader reader("../../test-sets/sets_100000_1000_32_1574465740.txt");

  reader.skip_lines(3); // skip 3 lines

  int lg_j, lg_k, lg_m;

  int diff_size = DIFF_SIZE;
  int diff_start = DIFF_START;
  int union_size = UNION_SIZE;
  int n_test = N_TEST;

  int t = DIFF_SIZE;

  float diff_est = -1.0;
  bool correct;

  std::vector<int> setA, setB;
  setB.resize(union_size - diff_size);

  unordered_set<int> diff; // needed when checking whether successfully decoded

  std::ifstream fest;

  if (USE_EST) {
    fest.open(ESTDIFFSIZE_FILE);
    if (!fest.is_open()) {
      fprintf(stderr, "Failed to open %s\n", ESTDIFFSIZE_FILE);
      exit(1);
    }
  }

  SimpleTimer timer;
  double t_encoding, t_decoding;

  fout << "#tid,transmitted_bytes,succeed,encoding_time,decoding_time,"
          "succeed_,true_diff,num_cells,key_bytes,est_diff\n";

  const std::vector<uint8_t> VAL{0};
  for (int i = 0; i < n_test; ++i) {
    reader.read<int>(setA, union_size);

    if (USE_EST) {
      // In the case where the ground truth value of the size
      // of the set difference is not known.
      fest >> diff_est;
      debug("Get estimate %.6f\n", diff_est);
      t = int(ceil(diff_est));
    }

    for (lg_j = 0, lg_k = 0; lg_j < diff_start; ++lg_j, ++lg_k) {
      setB[lg_k] = setA[lg_j];
    }

    diff.clear();
    for (lg_m = 0; lg_m < diff_size; ++lg_m, ++lg_j) {
      diff.insert(setA[lg_j]);
    }

    for (; lg_j < union_size; ++lg_j, ++lg_k) {
      setB[lg_k] = setA[lg_j];
    }

    assert(lg_k == setB.size());

    timer.restart();
    /*
    IBLT ibltA(t, VAL_SIZE);
    IBLT ibltB(t, VAL_SIZE);
    */

    IBLT ibltA(t, VAL_SIZE, HEDGE, (t > 200 ? 3: 4));
    IBLT ibltB(t, VAL_SIZE, HEDGE, (t > 200 ? 3: 4));

    for (const auto x : setA) {
      ibltA.insert(x, VAL);
    }

    for (const auto y : setB) {
      ibltB.insert(y, VAL);
    }
    t_encoding = timer.elapsed();

    std::set<std::pair<uint64_t, std::vector<uint8_t>>> pos, neg;
    timer.restart();
    auto ibltD = ibltA - ibltB;
    bool succeed = ibltD.listEntries(pos, neg);
    t_decoding = timer.elapsed();

    correct = true;
    if (pos.size() + neg.size() != diff.size()) {
      correct = false;
    } else {
      for (const auto &p : pos) {
        if (diff.count(p.first) == 0) {
          correct = false;
          break;
        }
      }
      if (correct) {
        for (const auto &p : neg) {
          if (diff.count(p.first) == 0) {
            correct = false;
            break;
          }
        }
      }
    }

    if (succeed && correct) {
      fout << (i + 1) << "," << (BYTES_EACH_CELL * ibltA.hashTableSize()) << ","
           << 1 << "," << fixed << t_encoding << "," << fixed << t_decoding
           << ","  << succeed << "," << DIFF_SIZE << "," << ibltA.hashTableSize() << ","
           << KEY_SIZE << "," << t << "\n";
    } else {
      fout << (i + 1) << "," << (BYTES_EACH_CELL * ibltA.hashTableSize()) << ","
           << (correct ? 0 : -1) << "," << fixed << t_encoding << "," << fixed
           << t_decoding << ","  << succeed << "," << DIFF_SIZE << "," << ibltA.hashTableSize()
           << "," << KEY_SIZE << "," << t << "\n";
    }
  }
}
