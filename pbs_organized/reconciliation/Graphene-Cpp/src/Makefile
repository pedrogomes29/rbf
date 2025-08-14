CXXFLAGS = -Wall -O3 -I. -I./bloom_filter -I../IBLT-optimization -std=c++11
LDFLAGS = 
RM = gio trash


TARGETS = search_params_test grahene grahene_OLD
TEST_FILES = $(wildcard ../experiment1/test_sets_10000_*.txt) 

all: grahene

search_params_test: test_search_params.py params search_params.py
	./test_search_params.py

params: search_params_wrapper.cpp search_params.h setup.py
	python3 setup.py build_ext --inplace

grahene_OLD: graphene_protocol_1.cpp ../IBLT-optimization/iblt.cpp ../IBLT-optimization/utilstrencodings.cpp ../IBLT-optimization/murmurhash3.cpp
	$(CXX) $^ -o $@ $(CXXFLAGS) $(LDFLAGS)

grahene: graphene.cpp ../IBLT-optimization/iblt.cpp ../IBLT-optimization/utilstrencodings.cpp ../IBLT-optimization/murmurhash3.cpp
	$(CXX) $^ -o $@ $(CXXFLAGS) $(LDFLAGS)

grahene-dbg: graphene.cpp ../IBLT-optimization/iblt.cpp ../IBLT-optimization/utilstrencodings.cpp ../IBLT-optimization/murmurhash3.cpp
	$(CXX) $^ -o $@ $(CXXFLAGS) $(LDFLAGS) -DDEBUG

$(TEST_FILES): ../experiment1/graphene_original.py 
	python3 $<

grahene_test: grahene $(TEST_FILES)
	@echo "Test Graphene"
	chmod +x ./grahene
	./grahene -n 10 -d 10 -s 0 -u 10000 -i ../experiment1/test_sets_10000_9990.txt
	./grahene -n 10 -d 100 -s 0 -u 10000 -i ../experiment1/test_sets_10000_9900.txt
	./grahene -n 10 -d 1000 -s 0 -u 10000 -i ../experiment1/test_sets_10000_9000.txt
	@echo "Test completed"


test: search_params_test

clean:
	$(RM) -f $(TARGETS)