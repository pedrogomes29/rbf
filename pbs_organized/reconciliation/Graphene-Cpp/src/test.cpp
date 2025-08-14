#include <iostream>
#include <cstdio>
#include <string>
#include <cstring>
#include <vector>
#include <cstdlib>
#include "search_params.cpp"

using namespace std;
int main(){
	/*
	struct search_params sepa;
	double error_rate = 0.5;
	int capacity = 1000;
	double a = 0.1;
	double fpr = 0.5;
	int n = 1000;
	int y = 10;
	int x = 100;
	int m = 600;
	int rows;
	double min_a;
	double min_fpr;
	int min_iblt_rows;
	double bound = 0.9;
	int result;
	int z = 10;
	double delta;
	int mempool_size = 10;
	int blk_size = 10;
	result = sepa.search_x_star(z, mempool_size, fpr, bound, blk_size);
	cout << result << endl;
	//cout << min_a << ' ' << min_fpr << ' ' << min_iblt_rows << endl;
	*/

	/*
	string TEST_SETS = "../../test-sets/sets_100000_1000_32_1574465740.txt";
	FILE* set_fd = fopen(TEST_SETS.c_str(), "r");
	char buf[1100000];
	for(int i = 0; i < 3; ++i){
		fgets(buf, 1100000, set_fd);
		printf("%d\n", strlen(buf));
	}
	vector<int> elements;
	fgets(buf, 1100000, set_fd);
	char* ptr = strtok(buf, " ");
		while(ptr != NULL){
		elements.push_back(atoi(ptr));
		ptr = strtok(NULL, " ");
	}
	cout << elements.size() << endl;
	vector<int> blk;
	blk.insert(blk.end(), elements.begin(), elements.begin() + 1520);
	cout << blk.size() << endl;
	blk.insert(blk.end(), elements.begin() + 1520 + 1000, elements.begin() + 100000);
	cout << blk.size() << endl;
	fclose(set_fd);
	*/

	struct search_params params = search_params();
	return 0;
}