#include <iostream>
#include <algorithm>
#include <random>
#include <cmath>
#include <string>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <ctime>
#include <set>
#include <unordered_set>
#include "search_params.h"
#include "bloom_filter/bloom_filter.hpp"
#include "../IBLT-optimization/iblt.h"
#include "../IBLT-optimization/utilstrencodings.h"

#define TXN_SHORT_BYTES_CB 6
#define TXN_SHORT_BYTES 4  // 8
#define BITSIZE TXN_SHORT_BYTES * 8
#define TAU 12  // bytes per IBLT cell
using namespace std;

default_random_engine e;

int BLK_SIZE[3] = {200, 2000, 10000};
int len_blk = 3;

double B[1] = {1.0/240};
int len_bound = 1;

int NUM_TRIAL = 10;

int DIFF_SIZES[1] = {1000};
int DIFF_STARTS[1] = {1520}; //for convenience, from diff_starter.json
int len_diff = 1;

int UNION_SIZE = 100000;

double FRACTION[1] = {1.0};
int len_fraction = 1;

/*
void create_mempools(int mempool_size,  int blk_size, 
					vector<unsigned> & blk, vector<unsigned> & receiver_mempool){
	blk.resize(blk_size); //32bit-long, use uint for convenience
	uniform_int_distribution<unsigned> gen(0, UINT32_MAX);
	for(int i = 0; i < blk_size; ++i){
		blk[i] = gen(e);
	}
	vector<unsigned> in_blk(blk);
	int num_doesnt_have = mempool_size - blk_size;
	vector<unsigned> in_mempool(num_doesnt_have);
	for(int i = 0; i < num_doesnt_have; ++i){
		in_mempool[i] = gen(e);
	}
	receiver_mempool = in_blk;
	receiver_mempool.insert(receiver_mempool.end(), in_mempool.begin(), in_mempool.end());
}
*/

bool decode_blk(const set<pair<uint64_t,vector<uint8_t> > > & positive,
				const set<pair<uint64_t,vector<uint8_t> > > & negative,
				const vector<int> & passed,
				const vector<int> & blk,
				unordered_set<int> & in_blk,
				int & t_decoding){
	unordered_set<int> not_in_blk;
	clock_t t_s = clock();
	set<pair<uint64_t,vector<uint8_t> > >::iterator it;
	for(it = positive.begin(); it != positive.end(); ++it){
		not_in_blk.insert(int(it->first));
	}
	for(it = negative.begin(); it != negative.end(); ++it){
		in_blk.insert(int(it->first));
	}
	clock_t t_e = clock();
	t_decoding = round(1000.0 * (t_e - t_s) / (double)CLOCKS_PER_SEC);

	unordered_set<int> possibly_in_blk(passed.begin(), passed.end());
	unordered_set<int>::iterator i;

	// difference update 
	for(i = not_in_blk.begin(); i != not_in_blk.end(); ++i){
		possibly_in_blk.erase(*i);
	}
	unordered_set<int> reconstructed_blk;

	//union
	for(i = possibly_in_blk.begin(); i != possibly_in_blk.end(); ++i){
		reconstructed_blk.insert(*i);
	}
	for(i = in_blk.begin(); i != in_blk.end(); ++i){
		reconstructed_blk.insert(*i);
	}
	unordered_set<int> set_blk(blk.begin(), blk.end());
	return reconstructed_blk == set_blk;
}

void trial(FILE* fd){
	struct search_params params = search_params();
	for(int i = 0; i < len_diff; ++i){

		int diff_size = DIFF_SIZES[i];
		int true_false_positives = diff_size;

		string graphene_name = to_string(UNION_SIZE) + "_" + to_string(diff_size) + "_0_Graphene.txt";
		FILE* o_fp = fopen(graphene_name.c_str(), "w");
		fprintf(o_fp, "#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,ibt_ratio,scaling_ratio\n");
		
		string TEST_SETS = "../../test-sets/sets_100000_1000_32_1574465740.txt";
		FILE* set_fd = fopen(TEST_SETS.c_str(), "r");
		char buf[100];
		for(int j = 0; j < 3; ++j)
			fgets(buf, 99, set_fd);

		for(int j = 0; j < len_bound; ++j){
			double bound = B[j];

			for(int k = 0; k < len_fraction; ++k){
				double fraction = FRACTION[k];

				// True_positives is the number of txns in the blk the receiver has
				int true_positives = UNION_SIZE - true_false_positives; // int(blk_size * fraction)
				int mempool_size = true_false_positives + true_positives;

				printf("Running %d trials for parameter combination: extra txns in mempool %d diff size %d fraction %lf\n",
					NUM_TRIAL, true_false_positives, diff_size, fraction);

				// Size of Compact block (inv + getdata)
                // getdata = (1 - fraction) * blk_size * TXN_SHORT_BYTES_CB
                // inv = blk_size * TXN_SHORT_BYTES_CB
                // compact = inv + getdata
                int compact = 0;

				for(int x = 0; x < NUM_TRIAL; ++x){
					cout << x + 1 << endl;
					char line[1100000];
					fgets(line, 1100000, set_fd);
					vector<int> elements;
					char * ptr = strtok(line, " ");
					while(ptr != NULL) {
						elements.push_back(atoi(ptr));
						ptr = strtok(NULL, " ");
					}
					vector<int> blk;
					blk.insert(blk.end(), elements.begin(), elements.begin() + DIFF_STARTS[i]);
					blk.insert(blk.end(), elements.begin() + DIFF_STARTS[i] + diff_size, elements.begin() + UNION_SIZE);
					vector<int> receiver_mempool(elements);
					//Do we use diffs later?
					vector<int> diffs;
					diffs.insert(diffs.end(), elements.begin() + DIFF_STARTS[i], elements.begin() + DIFF_STARTS[i] + diff_size);
					int blk_size = blk.size();
					// Sender creates BF of blk
					clock_t t_s = clock();
					double a, fpr_sender;
					int iblt_rows_first;
					params.solve_a(mempool_size, blk_size, blk_size, 0, a, fpr_sender, iblt_rows_first);
					bloom_parameters parameters;
					parameters.projected_element_count = blk_size;
					parameters.false_positive_probability = fpr_sender;
					parameters.compute_optimal_parameters();
					bloom_filter bloom_sender = bloom_filter(parameters);
					double tmp = blk_size + 0.5;
					//num_slices = hash_count
					//num_bits = size
					double exponent = (-int(bloom_sender.hash_count()) * tmp / (int(bloom_sender.size()) - 1));
					double real_fpr_sender = 1 - pow(1 - exp(exponent), bloom_sender.hash_count());

					// Sender creates IBLT of blk
					double a_old = a;
					// CHANGED: here we re-calculate `a` based on `real_fpr_sender`
					a = real_fpr_sender * (mempool_size - blk_size);
					double beta = 239.0/240;
					double s = -log(1.0 - beta) / a;
					// Using Chernoff Bound
					double delta = 0.5 * (s + sqrt(s + sqrt(s * s + 8.0 * s)));
					double a_star = (1 + delta) * a;
					a = ceil(a_star);
					int iblt_rows_first_old = iblt_rows_first;

					if(a - 1 >= 1000)
						iblt_rows_first = ceil(1.362549 * a);
					else
						iblt_rows_first = params.params[int(a) - 1].size;
					IBLT iblt_sender_first = IBLT(int(a), TXN_SHORT_BYTES);

					// Add to BF and IBLT
					int len_blk = blk.size();
					for(int t = 0; t < len_blk; ++t){
						int txn = blk[t];
						bloom_sender.insert(txn);
						iblt_sender_first.insert(txn, ParseHex("20202030"));
					}

					// Receiver computes how many items pass through BF of sender and creates IBLT
					IBLT iblt_receiver_first = IBLT(round(a), TXN_SHORT_BYTES);
					vector<int> Z;
					int len_rec_pool = receiver_mempool.size();
					for(int t = 0; t < len_rec_pool; ++t){
						int txn = receiver_mempool[t];
						if (bloom_sender.contains(txn)){
							Z.push_back(txn);
							iblt_receiver_first.insert(txn, ParseHex("20202030"));
						}
					}

					clock_t t_e = clock();
					int t_encoding = round(1000.0 * (t_e - t_s) / (double)CLOCKS_PER_SEC);

					t_s = clock();
					int z = Z.size();
					int observed_false_positives = z - true_positives;

					// Eppstein subtraction
					IBLT T = iblt_receiver_first - iblt_sender_first;
					set<pair<uint64_t,vector<uint8_t> > > positive;
					set<pair<uint64_t,vector<uint8_t> > > negative;
					bool success = T.listEntries(positive, negative);
					t_e = clock();
					int t_decoding = round(1000.0 * (t_e - t_s) / (double)CLOCKS_PER_SEC);

					// Check whether decoding successful
					if(success){
						unordered_set<int> in_blk;
						int decoding_time;
						bool flag = decode_blk(positive, negative, Z, blk, in_blk, decoding_time);
						t_decoding += decoding_time;

						// Each component of graphene blk size
						int first_IBLT = iblt_rows_first * TAU;
						int first_BF = ceil(bloom_sender.size() / 8.0);
						int extra = in_blk.size() * TXN_SHORT_BYTES;

						// Compute size of Graphene block
						int graphene = first_IBLT + first_BF + extra;

						// '#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,num_recovered,num_cells,num_hashes,first_BF,first_BF_fpr,first_IBLT,second_BF,second_BF_fpr,secondIBLT\n'
                        fprintf(o_fp, "%d,1,%d,%d,%d,%d,%lf,%lf\n",
                        	x + 1, graphene, int(flag), t_encoding, t_decoding,
                        	(first_IBLT + 0.0)/graphene, (first_IBLT + extra + 0.0)/graphene
                        );

                        // print(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                        //     fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                        //     real_fpr_sender) + '\t' + str(0) + '\t' + str(a) + '\t' + str(0) + '\t' + str(
                        //     0) + '\t' + str(0) + '\t' + str(z) + '\t' + str(0) + '\t' + str(
                        //     observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(False) + '\t' + str(
                        //     graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(0) + '\t' + str(
                        //     0) + '\t' + str(extra) + '\t' + str(iblt_rows_first) + '\t' + str(0) + '\t' + str(
                        //     compact))
                        fprintf(fd, "%d,%d,%lf,%lf,%d,%lf,%lf,0,%d,0,0,0,%d,0,%d,%d,False,%d,%d,%d,0,0,%d,%d,0,%d,%d,%d\n",
                        	true_false_positives, blk_size, bound, fraction, mempool_size, fpr_sender,
                        	real_fpr_sender, int(a), z, observed_false_positives, int(success && flag),
                        	graphene, first_IBLT, first_BF, extra, iblt_rows_first, compact,
                        	int(a_old), iblt_rows_first_old);
					}
					else{
						// Each component of graphene blk size
						int first_IBLT = iblt_rows_first * TAU;
						int first_BF = ceil(bloom_sender.size() / 8.0);
						int extra = 0;

						// Compute size of Graphene block
						int graphene = first_IBLT + first_BF + extra;

						// '#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,num_recovered,num_cells,num_hashes,first_BF,first_BF_fpr,first_IBLT,second_BF,second_BF_fpr,secondIBLT\n'
                        bool flag = false;
                        fprintf(o_fp, "%d,1,%d,%d,%d,%d,%lf,%lf\n",
                        	x + 1, graphene, int(flag), t_encoding, t_decoding,
                        	(first_IBLT + 0.0)/graphene, (first_IBLT + extra + 0.0)/graphene
                        );

                        // print(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                        //     fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                        //     real_fpr_sender) + '\t' + str(0) + '\t' + str(a) + '\t' + str(0) + '\t' + str(
                        //     0) + '\t' + str(0) + '\t' + str(z) + '\t' + str(0) + '\t' + str(
                        //     observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(False) + '\t' + str(
                        //     graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(0) + '\t' + str(
                        //     0) + '\t' + str(extra) + '\t' + str(iblt_rows_first) + '\t' + str(0) + '\t' + str(
                        //     compact))
                        fprintf(fd, "%d,%d,%lf,%lf,%d,%lf,%lf,0,%d,0,0,0,%d,0,%d,%d,False,%d,%d,%d,0,0,%d,%d,0,%d,%d,%d\n",
                        	true_false_positives, blk_size, bound, fraction, mempool_size, fpr_sender,
                        	real_fpr_sender, int(a), z, observed_false_positives, int(success && flag),
                        	graphene, first_IBLT, first_BF, extra, iblt_rows_first, compact,
                        	int(a_old), iblt_rows_first_old);
                        fflush(fd);
					}
				}
			}
		}
		fclose(o_fp);
		fclose(set_fd);
	}
}

int main(){
	/*
	vector<unsigned> blk, receiver_mempool;
	create_mempools(10, 5, blk, receiver_mempool);
	for(int i = 0; i < 5; ++i){
		cout << blk[i] << endl;
	}
	for(int i = 0; i < 10; ++i){
		cout << receiver_mempool[i] << endl;
	}
	*/
	uniform_int_distribution<unsigned> gen(0, UINT32_MAX);
	string csvname = "results/protocol-I-CB-" + to_string(gen(e) >> 7) + ".csv";
	FILE* fd = fopen(csvname.c_str(), "w");
	trial(fd);
	fclose(fd);
	return 0;
}