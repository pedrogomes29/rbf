#include <cassert>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <math.h>
#include <minisketch.h>
#include <string.h>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <xxhash.h>

#include "FileReader.h"
#include "SimpleTimer.h"

using namespace std;

const int KEY_BITS = 32;

uint myhash(uint key, uint seed) { return XXH32(&key, sizeof(key), seed); }

void Encode(const vector<uint> &set, vector<int> &bit, vector<int> &loc,
            uint seed) {
  int len = set.size();
  int n = bit.size();
  memset(&bit[0], 0, n * sizeof(int));
  for (int i = 0; i < len; ++i) {
    /*
    loc[i] = myhash(set[i], seed) % n;
    bit[loc[i]] ^= 1;
    */
    // make sure no one goes into the bin with id 0
    // since minisketch does not support it right now
    loc[i] = (myhash(set[i], seed) % (n - 1)) + 1;
    bit[loc[i]] ^= 1;
  }
}

unordered_map<int, pair<int /* bch length */, int /* bch decoding capacity */>>
loadBestParam(int round) {
  assert(round == 2 || round == 3);

#ifdef CLION_DEBUG
  auto parameter_file = string("../params_r") + to_string(round) + "_vs_graphene.csv";
#else
  auto parameter_file = string("./params_r") + to_string(round) + "_vs_graphene.csv";
#endif
  unordered_map<int, pair<int, int>> parameters{};

  string line;
  ifstream myfile(parameter_file);
  if (!myfile.is_open()) {
    std::cout << "Unable to open parameter file: " << parameter_file << "\n";
    exit(-1);
  }
  // getline(myfile, line);
  std::string results[4];

  while (getline(myfile, line)) {
    std::istringstream iss(line);
    int j = 0;
    while (std::getline(iss, results[j], ',')) {
      j++;
    }
    int expected_diff_size = std::stoi(results[0]);
    int bch_length = std::stoi(results[2]);
    int bch_capacity = std::stoi(results[3]);
    assert(parameters.count(expected_diff_size) == 0);
    parameters[expected_diff_size] = {bch_length, bch_capacity};
  }
  myfile.close();

  return parameters;
}

void usage(const char *progname) {
  printf("Usage: %s NTEST UNIONSIZE DIFFSIZE DELTA BCHLOGN BCHT FAILNUM "
         "DIFFSTART ROUNDFOR99 [ESTFILENAME ESTINFLATIONRATIO]\n",
         progname);

  exit(1);
}

int main(int argc, char **argv) {

  char *progname;
  char *p;

  progname = ((p = strrchr(argv[0], '/')) ? ++p : argv[0]);

  if (!(argc == 10 || argc == 12))
    usage(progname);

  int ntest = atoi(argv[1]);    // number of tests
  int setsize = atoi(argv[2]);  // set size(B's size might be $setsize-1)
  int diffsize = atoi(argv[3]); // symmetric difference's size (A have
                                // ceil(diffsize/2),B have floor(diffsize/2))
  float delta = atof(argv[4]);  // subset number/$diffsize
  int logn = atoi(argv[5]);     // length of BCH code
  int n = (1 << logn) - 1; // number of bins in the second layer of each group
  int t = atoi(argv[6]);   // error correction capability
  int failnum = atoi(argv[7]); // if decode fails(too many errors), divide into
                               // $failnum subsets

  int diff_start = atoi(argv[8]);

  char *est_filename = nullptr;
  float diff_est = diffsize;
  float EST_INFLATION_RATIO = 1.0;

  int assumed_diffsize = diffsize;
  int round99 =
      atoi(argv[9]); // maximum desired rounds for achieving 99% success rate

  if (argc > 11) {
    assert(argc == 12);
    est_filename = argv[10];
    EST_INFLATION_RATIO = atof(argv[11]);
  }

  int checksumlen = 32; // length of checksum
  int decodeheaderlen = ceil(log2(t + 2));
  int checkheaderlen = ceil(log2(t + 1)) + 1;
  int paritylen = logn * t;

  ofstream fout;
  fout.open(to_string(setsize) + "_" + to_string(diffsize) + "_" +
            to_string(delta) + "_" + (est_filename ? "1" : "0") + "_r" +
            to_string(round99) + "_communication_ITReconAgainstGraphene.txt");

  ofstream tfout;
  tfout.open(string("exectimedetails-") + to_string(setsize) + "_" + to_string(diffsize) + "_" +
             to_string(delta) + "_" + (est_filename ? "1" : "0") + "_r" +
             to_string(round99) + "_executiontime_ITReconAgainstGraphene.txt");

  fout << setw(15) << "ntest" << setw(15) << ntest << endl;
  fout << setw(15) << "setsize" << setw(15) << setsize << endl;
  fout << setw(15) << "diffsize" << setw(15) << diffsize << endl;
  fout << setw(15) << "delta" << setw(15) << delta << endl;
  // fout << setw(15) << "logn" << setw(15) << logn << endl;
  // fout << setw(15) << "t" << setw(15) << t << endl;
  fout << setw(15) << "failnum" << setw(15) << failnum << endl;
  fout << setw(15) << "round99" << setw(15) << round99 << endl;

  tfout << setw(15) << "ntest" << setw(15) << ntest << endl;
  tfout << setw(15) << "setsize" << setw(15) << setsize << endl;
  tfout << setw(15) << "diffsize" << setw(15) << diffsize << endl;
  tfout << setw(15) << "delta" << setw(15) << delta << endl;
  tfout << setw(15) << "failnum" << setw(15) << failnum << endl;
  tfout << setw(15) << "round99" << setw(15) << round99 << endl;

  fout << "#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,"
          "truerec,falserec,paritybits,"
          "xornum,checksumbits,decodebits,checkbits,logn,t,assumed_diff_size\n";
  tfout << "#tid,round,t_partition,t_encodebit,t_encodebch,t_decodebch,t_"
           "decodexor,t_check,t_encoding,t_decoding,logn,t,assumed_diff_size\n";

  vector<uint> seeds(ntest);
  ifstream myfile;
  myfile.open("seedpool.txt");
  for (int i = 0; i < ntest; ++i) {
    myfile >> seeds[i];
  }
  myfile.close();

  /*
  int unionsize = (2 * setsize - diffsize) / 2;
  int dasize = (diffsize + 1) / 2;
  int dbsize = diffsize / 2;
  int setasize = setsize, setbsize = unionsize + dbsize;
  vector<uint> setA(setsize), setB(setsize);
  myfile.open("keypool.txt");
  for (int i = 0; i < setasize; ++i) {
          myfile >> setA[i];
  }
  for (int i = 0; i < unionsize; ++i) {
          setB[i] = setA[i];
  }
  for(int i = unionsize; i < setbsize; ++i){
          myfile >> setB[i];
  }
  myfile.close();
  unordered_set<uint> diff;
  for(int i = unionsize; i < setasize; ++i){
          diff.insert(setA[i]);
  }
  for(int i = unionsize; i < setbsize; ++i){
          diff.insert(setB[i]);
  }
  */

  //
#ifdef CLION_DEBUG
  TxTFileReader reader("../../test-sets/sets_100000_1000_32_1574465740.txt");
#else
  TxTFileReader reader("../test-sets/sets_100000_1000_32_1574465740.txt");
#endif
  reader.skip_lines(3); // skip 3 lines

  vector<int> setA, setB;
  unordered_set<uint> diff;
  int setasize, setbsize;

  int originsubnum = ceil(delta * diffsize);

  int lg_j = 0, lg_k = 0, lg_m = 0;

  setB.resize(setsize - diffsize);

  SimpleTimer timer;

  std::ifstream fest;

  // load best parameters
  unordered_map<int, pair<int, int>> best_params = loadBestParam(round99);

  // load estimates
  if (est_filename != nullptr) {
    fest.open(est_filename);
    if (!fest.is_open()) {
      fprintf(stderr, "Failed to open %s\n", est_filename);
      exit(1);
    }
  }

  for (int i = 0; i < ntest; ++i) {
    reader.read<int>(setA, setsize);

    for (lg_j = 0, lg_k = 0; lg_j < diff_start; ++lg_j, ++lg_k) {
      setB[lg_k] = setA[lg_j];
    }

    for (lg_m = 0; lg_m < diffsize; ++lg_m, ++lg_j) {
      diff.insert(setA[lg_j]);
    }

    for (; lg_j < setsize; ++lg_j, ++lg_k) {
      setB[lg_k] = setA[lg_j];
    }

    assert(lg_k == setB.size());

    setasize = setA.size();
    setbsize = setB.size();

    if (est_filename != nullptr) {
      // In the case where the ground truth value of the size
      // of the set difference is not known.
      fest >> diff_est;

      // our set reconciliation will assume the size of the set difference
      // is `assumed_diffsize`
      assumed_diffsize = int(ceil(diff_est * EST_INFLATION_RATIO));
    }

    // partition
    timer.restart();
    int subnum = ceil(delta * assumed_diffsize); // originsubnum;
    originsubnum = subnum;
    vector<vector<uint>> subA(subnum);
    vector<vector<uint>> subB(subnum);
    vector<int> gnum(subnum);
    vector<uint> reconciled;

    for (int j = 0; j < setasize; ++j) {
      int index = myhash(setA[j], seeds[i]) % subnum;
      subA[index].push_back(setA[j]);
    }
    for (int j = 0; j < setbsize; ++j) {
      int index = myhash(setB[j], seeds[i]) % subnum;
      subB[index].push_back(setB[j]);
    }
    for (int j = 0; j < subnum; ++j) {
      gnum[j] = j;
    }
    double t_partition = timer.elapsed();

#ifdef DEBUG
    // just use user specific parameters
#else
    // load params
    assert(best_params.count(assumed_diffsize) > 0);
    auto param_pair = best_params[assumed_diffsize];
    logn = param_pair.first;
    t = param_pair.second;
#endif

    n = (1 << logn) - 1;
    decodeheaderlen = ceil(log2(t + 2));
    checkheaderlen = ceil(log2(t + 1)) + 1;
    paritylen = logn * t;

    int nround = 1;
    vector<int> paritybits;
    vector<int> xornum;
    vector<int> checksumbits;
    vector<int> decodebits;
    vector<int> checkbits;
    vector<int> truerec;
    vector<int> falserec;

    vector<double> t_encoding, t_decoding;

    while (subnum) {

      double t_encodebit = 0;
      double t_encodebch = 0;
      double t_decodebch = 0;
      double t_decodexor = 0;
      double t_check = 0;

      paritybits.push_back(subnum * paritylen);
      checksumbits.push_back(subnum * checksumlen);

      int xorcount = 0;
      int truecount = 0;
      int falsecount = 0;
      int decodebit = subnum * decodeheaderlen;
      int checkbit = subnum * checkheaderlen;

      vector<int> failed_subsets;

      for (int j = 0; j < subnum; ++j) {
        timer.restart();
        int subasize = subA[j].size();
        int subbsize = subB[j].size();
        vector<int> bitA(n);
        vector<int> bitB(n);
        vector<int> locA(subasize);
        vector<int> locB(subbsize);
        // balls into bins randomly
        Encode(subA[j], bitA, locA, seeds[i] + nround);
        Encode(subB[j], bitB, locB, seeds[i] + nround);
        t_encodebit += timer.elapsed();

        // BCH encoding
        timer.restart();
        minisketch *sketch_a = minisketch_create(logn, 0, t);
        minisketch *sketch_b = minisketch_create(logn, 0, t);
        for (int k = 0; k < n; ++k) {
          if (bitA[k])
            minisketch_add_uint64(sketch_a, k);
        }
        for (int k = 0; k < n; ++k) {
          if (bitB[k])
            minisketch_add_uint64(sketch_b, k);
        }
        t_encodebch += timer.elapsed();

        // BCH decoding
        timer.restart();
        vector<uint64_t> pos(t);
        minisketch_merge(sketch_b, sketch_a);
        int p = minisketch_decode(sketch_b, t, &pos[0]);
        minisketch_destroy(sketch_a);
        minisketch_destroy(sketch_b);
        t_decodebch += timer.elapsed();

        if (p >= 0) { // decoding succeeded

          xorcount += p;
          decodebit += p * logn;

          // calculate XORs
          timer.restart();
          // ???: changed from (t+1) => (p+1)
          vector<uint> XOR(p + 1);
          vector<int> ind(n);
          memset(&XOR[0], 0, sizeof(uint) * (p + 1));
          memset(&ind[0], 0, sizeof(int) * n);

          for (int k = 0; k < p; ++k) {
            ind[pos[k]] = k + 1;
          }
          for (int k = 0; k < subasize; ++k) {
            int tmp = subA[j][k];
            XOR[ind[locA[k]]] ^= tmp;
          }
          for (int k = 0; k < subbsize; ++k) {
            int tmp = subB[j][k];
            XOR[ind[locB[k]]] ^= tmp;
          }
          t_decodexor += timer.elapsed();

          timer.restart();
          // The XORs of all the elements in the buckets whose
          // does not contain any balls should be zero!
          // If it is not ===> collision happens (even number of balls go into
          // the same bin)
          if (XOR[0] != 0) {
            int oldsize = subA.size();
            subA.resize(oldsize + 1);
            subB.resize(oldsize + 1);
            gnum.resize(oldsize + 1);
            for (int k = 0; k < subasize; ++k) {
              if (!ind[locA[k]]) {
                subA[oldsize].push_back(subA[j][k]);
              }
            }
            for (int k = 0; k < subbsize; ++k) {
              if (!ind[locB[k]]) {
                subB[oldsize].push_back(subB[j][k]);
              }
            }
            gnum[oldsize] = gnum[j];
          }

          for (int k = 1; k <= p; ++k) {
            if (XOR[k]) {
              // if (myhash(XOR[k], seeds[i] + nround) % n == pos[k - 1] &&
              //     myhash(XOR[k], seeds[i]) % originsubnum == gnum[j]) {
              if (myhash(XOR[k], seeds[i] + nround) % (n - 1) + 1 ==
                      pos[k - 1] &&
                  myhash(XOR[k], seeds[i]) % originsubnum == gnum[j]) {
                reconciled.push_back(XOR[k]);
                if (diff.count(XOR[k]))
                  ++truecount;
                else
                  ++falsecount;
              } else {
                checkbit += logn;
                int oldsize = subA.size();
                subA.resize(oldsize + 1);
                subB.resize(oldsize + 1);
                gnum.resize(oldsize + 1);
                for (int q = 0; q < subasize; ++q) {
                  if (locA[q] == pos[k - 1]) {
                    subA[oldsize].push_back(subA[j][q]);
                  }
                }
                for (int q = 0; q < subbsize; ++q) {
                  if (locB[q] == pos[k - 1]) {
                    subB[oldsize].push_back(subB[j][q]);
                  }
                }
                gnum[oldsize] = gnum[j];
              }
            }
          }
          t_check += timer.elapsed();
        } else {
          failed_subsets.push_back(j);
        }
      }

      auto t_encoding_this_round = t_partition + t_encodebit + t_encodebch;
      auto t_decoding_this_round = t_decodexor + t_encodebch + t_check;
      // recording execution time
      tfout << nround << "," << fixed << t_partition << "," << fixed
            << t_encodebit << "," << fixed << t_encodebch << "," << fixed
            << t_decodebch << "," << fixed << t_decodexor << "," << fixed
            << t_check << "," << fixed
            << t_partition + t_encodebit + t_encodebch << "," << fixed
            << t_decodexor + t_encodebch + t_check << "," << logn << "," << t
            << "," << assumed_diffsize << "\n";

      t_partition = 0;
      if (!failed_subsets.empty()) {
        timer.restart();
        for (auto j : failed_subsets) {
          int oldsize = subA.size();
          int subasize = subA[j].size();
          int subbsize = subB[j].size();
          subA.resize(oldsize + failnum);
          subB.resize(oldsize + failnum);
          gnum.resize(oldsize + failnum);
          for (int k = 0; k < subasize; ++k) {
            int index = myhash(subA[j][k], seeds[i] + nround) % failnum;
            subA[oldsize + index].push_back(subA[j][k]);
          }
          for (int k = 0; k < subbsize; ++k) {
            int index = myhash(subB[j][k], seeds[i] + nround) % failnum;
            subB[oldsize + index].push_back(subB[j][k]);
          }
          for (int k = 0; k < failnum; ++k) {
            gnum[oldsize + k] = gnum[j];
          }
        }
        t_partition += timer.elapsed();
      }

      xornum.push_back(xorcount);
      decodebits.push_back(decodebit);
      checkbits.push_back(checkbit);
      truerec.push_back(truecount);
      falserec.push_back(falsecount);
      t_encoding.push_back(t_encoding_this_round);
      t_decoding.push_back(t_decoding_this_round);

      // update number of groups
      subA.erase(subA.begin(), subA.begin() + subnum);
      subB.erase(subB.begin(), subB.begin() + subnum);
      gnum.erase(gnum.begin(), gnum.begin() + subnum);
      subnum = subA.size();
      ++nround;
    }

    // fout << setw(5) << "round" << setw(14) << "truerec" << setw(14)
    //      << "falserec" << setw(14) << "paritybits" << setw(14) << "xornum"
    //      << setw(14) << "checksumbits" << setw(14) << "decodebits" <<
    //      setw(14)
    //      << "checkbits" << endl;
    int recovered = 0;
    for (int j = 0; j < nround - 1; ++j) {
      recovered += truerec[j];
      fout << (i + 1) << "," << (j + 1) << "," << fixed
           << (paritybits[j] + checksumbits[j] + decodebits[j] + checkbits[j] +
               xornum[j] * KEY_BITS) /
                  8.0
           << "," << (recovered == diffsize ? 1 : 0) << "," << fixed
           << t_encoding[j] << "," << fixed << t_decoding[j] << ","
           << truerec[j] << "," << falserec[j] << "," << paritybits[j] << ","
           << xornum[j] << "," << checksumbits[j] << "," << decodebits[j] << ","
           << checkbits[j] << "," << logn << "," << t << "," << assumed_diffsize
           << "\n";
    }
  }

  fout.close();
  tfout.close();
  return 0;
}