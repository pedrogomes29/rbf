// C++ implementation for Graphene
//
#include <cassert>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <getopt.h>
#include <iomanip>
#include <random>
#include <set>
#include <unordered_set>
#include <utility>
#include <vector>

#include "FileReader.h"
#include "FileSysUtil.h"
#include "SimpleTimer.h"
#include "bloom_filter.hpp"
#include "iblt.h"
#include "search_params.h"

using namespace std;

#define TXN_SHORT_BYTES 4
#define MAX_FILENAME_LEN 512

#ifdef DEBUG
#define debug(...) fprintf(stdout, __VA_ARGS__)
#else
#define debug(...)
#endif

const int TAU = 12; // bytes per IBLT cell
// chernoff bound
const double DEFAULT_CB = (1.0 - 239.0 / 240);
const int MAX_DIFF_IN_PARAM_FILE = 1000;

int N_TEST = 0;
int DIFF_SIZE = 0;
int DIFF_START = -1;
int UNION_SIZE = 0;
char SET_FILE[MAX_FILENAME_LEN] =
    "../test-sets/sets_100000_1000_32_1574465740.txt";
const char *RESULT_FOLDER_PREFIX = "result_";

std::string randomDirname() {
  std::random_device grnd;
  return std::string(RESULT_FOLDER_PREFIX) + to_string(grnd());
}

void usage(const char *progname) {
  printf("Usage: %s -n NTEST -d DIFFSIZE -s DIFFSTART -u UNIONSIZE -i "
         "INPUTSETFILENAME\n",
         progname);
  exit(1);
}

// Parse all arguments from command line
void arg_parse(int argc, char *argv[]) {
  int c;
  char *progname;
  char *p;
  // get the name of this program
  progname = ((p = strrchr(argv[0], '/')) ? ++p : argv[0]);
  while (true) {
    static struct option long_options[] = {
        {"ntest", required_argument, nullptr, 'n'},
        {"diffsize", required_argument, nullptr, 'd'},
        {"diffstart", required_argument, nullptr, 's'},
        {"unionsize", required_argument, nullptr, 'u'},
        {"inputfilename", optional_argument, nullptr, 'i'},
        {nullptr, 0, nullptr, 0}};
    /* getopt_long stores the option index here. */
    int option_index = 0;
    c = getopt_long(argc, argv, "n:d:s:u:hi:", long_options, &option_index);

    /* Detect the end of the options. */
    if (c == -1)
      break;

    switch (c) {
    case 'h':
      usage(progname);
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
    case 'i':
      debug("option -i with value `%s'\n", optarg);
      strcpy(SET_FILE, optarg);
      break;
    default:
      usage(progname);
    }
  }
  // verify arguments
  if (UNION_SIZE <= 0 || DIFF_SIZE <= 0 || N_TEST < 0 || DIFF_START == -1) {
    usage(progname);
  }
}

int main(int argc, char **argv) {
  arg_parse(argc, argv);

  // generate a result folder name & create a subfolder with this name
  auto res_folder = randomDirname();
  FileSysUtil::mkdirs(res_folder.c_str());
  printf("All results will be stored in the folder %s\n", res_folder.c_str());

  ofstream fout;
  // result filename
  auto filename = res_folder + "/" + to_string(UNION_SIZE) + "_" +
                  to_string(DIFF_SIZE) + "_" + to_string(N_TEST) +
                  "_Graphene.txt";
  fout.open(filename);
  if (!fout.is_open()) {
    fprintf(stderr, "Failed to open %s\n", filename.c_str());
    exit(1);
  }
  // write some meta information
  fout << setw(15) << "ntest" << setw(15) << N_TEST << endl;
  fout << setw(15) << "unionsize" << setw(15) << UNION_SIZE << endl;
  fout << setw(15) << "diffsize" << setw(15) << DIFF_SIZE << endl;
  fout << "# ====================================================\n";

  // write the header
  fout << "#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,"
          "fpr_cal,fpr_real,bf_size,iblt_size,ob_fps\n";

  cout << "#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,"
          "fpr_cal,fpr_real,bf_size,iblt_size,ob_fps\n";

  TxTFileReader reader(SET_FILE);
  reader.skip_lines(3); // skip 3 lines
  vector<int> setA /* mempool */, setB /* block */;
  // ground truth of the set difference
  // for checking whether the reconciliation is correct or not
  unordered_set<uint> diff;
  int setasize, setbsize;
  int lg_j = 0, lg_k = 0, lg_m = 0;
  setB.resize(UNION_SIZE - DIFF_SIZE);
  // dummy value for IBLT
  const std::vector<uint8_t> DUMMY_VAL{0};
  const int VAL_SIZE = 1; // bytes
  bool correct;
  double t_encoding, t_decoding;
  SimpleTimer timer;
  struct search_params params = search_params();
  bloom_parameters bf_params;
  double a, fpr_sender, real_fpr_sender;
  int iblt_rows_first;

  size_t failures = 0;

  for (int i = 0; i < N_TEST; ++i) {
    // input sets
    reader.read<int>(setA, UNION_SIZE);
    for (lg_j = 0, lg_k = 0; lg_j < DIFF_START; ++lg_j, ++lg_k) {
      setB[lg_k] = setA[lg_j];
    }
    diff.clear();
    for (lg_m = 0; lg_m < DIFF_SIZE; ++lg_m, ++lg_j) {
      diff.insert(setA[lg_j]);
      // std::cout << setA[lg_j] << " ";
    }
    // std::cout << std::endl;
    for (; lg_j < UNION_SIZE; ++lg_j, ++lg_k) {
      setB[lg_k] = setA[lg_j];
    }
    assert((size_t)lg_k == setB.size());

    setasize = setA.size();
    setbsize = setB.size();

    t_encoding = 0;
    t_decoding = 0;

    // Here, we need chernoff bound to make sure that the success probability
    // has guarantees
    /** NOTE: CB_solve_a allows `fpr_sender` to be 1. In such cases, we actually
     * DONOT need to create a Bloom filter. In addition, most Bloom filter
     * libraries requie `fpr` to be between 0 and 1 (excluding both 0 and 1).
     * However, the search space for `fpr_sender` in CB_solve_a guarantees that
     * it won't be 1. So we DONOT need worry about such cases. Actually,
     * optimzation space exists for this procedure, since in theory the optimal
     * value for `fpr_sender` could be 1. In such cases, if we ONLY use the
     * IBLT, we could save lots of computation efforts.
     *
     * In this implementation, like in the original Python implementation
     * provided by the authors of Graphene, we DONOT enable such an
     * optimization. **/
    params.CB_solve_a(setasize /* mempool_size */, setbsize /* blk_size */,
                      setbsize /* blk_size */, 0, DEFAULT_CB, a, fpr_sender,
                      iblt_rows_first);
#ifdef DEBUG
    printf("CB_slove_a results: a = %.2f, fpr = %.6f, iblt_rows_first = %.d\n",
           a, fpr_sender, iblt_rows_first);
#endif
    bool no_bf = (std::abs(1.0 - fpr_sender) < CONSIDER_TOBE_ZERO);
    std::unique_ptr<bloom_filter> bloom_sender_ptr; // empty ptr
    timer.restart();
    // create a Bloom filter
    if (!no_bf) {
      bf_params.projected_element_count = setbsize;
      bf_params.false_positive_probability = fpr_sender;
      bf_params.compute_optimal_parameters();
      // bloom_filter bloom_sender = bloom_filter(bf_params);
      std::unique_ptr<bloom_filter> temp_bf_ptr(new bloom_filter(bf_params));
      bloom_sender_ptr = std::move(temp_bf_ptr);
    }
    // create an IBLT
    IBLT iblt_sender_first = IBLT(int(a), VAL_SIZE);
    // Insert elements  into the bloom filter and IBLT

    for (auto elm : setB) {
      if (!no_bf)
        bloom_sender_ptr->insert(elm);
      iblt_sender_first.insert(elm /* key */, DUMMY_VAL /* (dummy) value */);
    }
    t_encoding = timer.elapsed();

    // ONLY for measurements:
    // Here, for all number of inserted elements (for the IBLT) larger than 1000
    // we use the parameters calculated for 1000, just like what did in the
    // original Python implementation. (Partially because the parameter tuning
    // procedure for IBLT is quite time-consuming)
    if (a - 1 >= MAX_DIFF_IN_PARAM_FILE)
      iblt_rows_first = ceil(1.362549 * a);
    else
      iblt_rows_first = params.params[int(a) - 1].size;
    if (!no_bf) {
      double tmp = setbsize + 0.5;
      double exponent = (-int(bloom_sender_ptr->hash_count()) * tmp /
                         (int(bloom_sender_ptr->size()) - 1));
      // Here, we use the fpr formula for bloom filter with any size
      // not the famous asymptotic one
      real_fpr_sender = pow(1 - exp(exponent), bloom_sender_ptr->hash_count());
    } else
      real_fpr_sender = 1.0;

    // Receiver computes how many items pass through BF of sender and creates
    // IBLT

    /* decode the BF */
    timer.restart();
    vector<int> Z;
    vector<int> Z_compl;
    if (!no_bf) {
      for (auto elm : setA) {
        if (bloom_sender_ptr->contains(elm))
          Z.push_back(elm);
        else
          Z_compl.push_back(elm);
      }
    }
    t_decoding = timer.elapsed();

    /* encode the IBF at the receiver side */
    timer.restart();
    auto iblt_receiver_first = IBLT(int(a), VAL_SIZE);
    if (no_bf) {
      for (auto elm : setA) {
        iblt_receiver_first.insert(elm, DUMMY_VAL);
      }
    } else {
      for (auto elm : Z) {
        iblt_receiver_first.insert(elm, DUMMY_VAL);
      }
    }
    t_encoding += timer.elapsed();

    /* decode the IBFs */
    timer.restart();
    std::set<std::pair<uint64_t, std::vector<uint8_t>>> pos, neg;
    // Eppstein subtraction
    auto ibltT = iblt_receiver_first - iblt_sender_first;
    bool correct = ibltT.listEntries(pos, neg);
    t_decoding += timer.elapsed();

    // for checking correctness
    size_t ob_fps = (setA.size() - Z_compl.size() - setB.size());
    std::cout << "Observed false positives: " << ob_fps << std::endl;
    // printf("Decoding failed\n");
    if (correct) {
      if (!(neg.empty() && (pos.size() + Z_compl.size() == diff.size()))) {
        // size mismatch
        printf("Size mismatch!\n");
        correct = false;
      } else {
        for (auto elm : Z_compl)
          if (diff.count(elm) == 0) {
            correct = false;
            break;
          }
        if (correct) {
          for (const auto &p : pos) {
            if (diff.count(p.first) == 0) {
              correct = false;
              break;
            }
          }
        }
      }
    }

    if (!correct)
      ++failures;

    // measurements
    float iblt_size = iblt_rows_first * TAU;
    float bf_size = no_bf ? 0 : (float)bloom_sender_ptr->size() / 8.0;
    // NOTE: Here, we ignore some tiny communication costs, such as those for
    // set size and false positive rate
    float communication = iblt_size + bf_size;

    // "#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,"
    //       "fpr_cal,fpr_real,bf_size,iblt_size\n";
    fout << (i + 1) << ","
         << "1," << fixed << communication << "," << (correct ? 1 : 0) << ","
         << fixed << t_encoding << "," << fixed << t_decoding << "," << fixed
         << fpr_sender << "," << fixed << real_fpr_sender << "," << fixed
         << bf_size << "," << fixed << iblt_size << "," << ob_fps << "\n";
    cout << (i + 1) << ","
         << "1," << fixed << communication << "," << (correct ? 1 : 0) << ","
         << fixed << t_encoding << "," << fixed << t_decoding << "," << fixed
         << setprecision(9) << fpr_sender << "," << fixed << setprecision(9)
         << real_fpr_sender << "," << fixed << bf_size << "," << fixed
         << iblt_size << "," << ob_fps << "\n";
  }
  printf("Total failures: %lu\n", failures);
  printf("Simulation DONE!\n\n");
  return 0;
}