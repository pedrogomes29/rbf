CXX = g++
RM = gio trash -f 

# difference between "=" and ":=", please refer to
# https://www.gnu.org/software/make/manual/html_node/Flavors.html
TOP := $(shell /bin/pwd)

BUILD = $(TOP)/build
SRCDIR = $(TOP)/src
PBS_BCH_PRARM_FILENAME_PREFIX = $(TOP)/perf/params_r${max_rounds}.csv
DATAOLDDIR = ../../test-sets/100000-1000
DATADIR = ../../test-sets/1000000-1000
PARAMDIR = ../params
EST_FILENAME_PATTERN = diff_estimates_with_tow_{d}_128_9012.txt
PRARM_FN_PREFIX = params_r
#
# Params used during revision (3 rounds, 5 diffs per group on average)
#
PRARM_FILENAME = params_r3_5_all.csv
PRARM_vs_GRAPHENE_FILENAME = params_r3_5_vs_graphene_all.csv
#
# Params used in the original submission (3 rounds, 5 diffs per group on average)
#
PRARM_FILENAME_OLD = params_r3.csv
PRARM_vs_GRAPHENE_FILENAME_OLD = params_r3_vs_graphene.csv
#
# Different avg (added during revision)
DIFF_AVGS = "3 7 10 15 20 25 30"
#
# Sets & diffs used during revision
#
LARGER_SETS = sets_1000000_1000_32_1574465740.txt
TEST_DIFFS = "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000 16000 30000 50000 100000"
#
# Sets & diffs used in the original submission
#
SETS = sets_100000_1000_32_1574465740.txt
TEST_DIFFS_OLD = "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000"


CXXFLAGS = -O3   -Wall  -std=c++11 -I$(SRCDIR)
LDFLAGS = -lminisketch -lxxhash

TARGET = $(BUILD)/pbs_perf 

all: $(TARGET)

$(BUILD)/pbs_perf_dbg: $(SRCDIR)/pbs.cpp
	@mkdir -p $(BUILD)
	cp $(SRCDIR)/seedpool.txt $(BUILD)
	-$(CXX) $(CXXFLAGS) $<  $(LDFLAGS) -o $@ -DDEBUG

debug: $(BUILD)/pbs_perf_dbg
	@echo building for debugging completed

$(BUILD)/pbs_perf: $(SRCDIR)/pbs.cpp
	@mkdir -p $(BUILD)
	-$(CXX) $(CXXFLAGS) $<  $(LDFLAGS) -o $@

$(BUILD)/pbs_perf_py_seeds: $(SRCDIR)/pbs.cpp
	@mkdir -p $(BUILD)
	-$(CXX) $(CXXFLAGS) -DUSE_PY_SEEDS $<  $(LDFLAGS) -o $@

$(BUILD)/test_random: $(SRCDIR)/test_random.cc 
	@mkdir -p $(BUILD)
	-$(CXX) $(CXXFLAGS) $<  $(LDFLAGS) -o $@

test: $(BUILD)/test_random
	@echo There following three should be different 
	$(BUILD)/test_random 10
	$(BUILD)/test_random 10
	$(BUILD)/test_random 10
	@echo There following three should be the same
	$(BUILD)/test_random 10 1297
	$(BUILD)/test_random 10 1297
	$(BUILD)/test_random 10 1297

$(BUILD)/pbs_experiments_diffs.sh: $(TOP)/cli_utils.py 
	@mkdir -p $(BUILD)
	@echo "Generate bash script pbs_experiments_diffs.sh ..." 
	$< -b ./pbs_perf -u 1000000 -d $(TEST_DIFFS) -p $(PARAMDIR)/$(PRARM_FILENAME) -e "$(DATADIR)/$(EST_FILENAME_PATTERN)" -g "5" -i $(DATADIR)/$(LARGER_SETS) -o $@
	@chmod +x $@

$(BUILD)/pbs_experiments_vs_graphene_diffs.sh: $(TOP)/cli_utils.py 
	@mkdir -p $(BUILD)
	@echo "Generate bash script pbs_experiments_vs_graphene_diffs.sh ..." 
	$< -b ./pbs_perf -u 1000000 -d $(TEST_DIFFS) -p $(PARAMDIR)/$(PRARM_vs_GRAPHENE_FILENAME) -e "$(DATADIR)/$(EST_FILENAME_PATTERN)" -g "5" -i $(DATADIR)/$(LARGER_SETS) -o $@
	@chmod +x $@

$(BUILD)/pbs_experiments_avg_diffs_per_group.sh: $(TOP)/cli_utils.py 
	@mkdir -p $(BUILD)
	@echo "Generate bash script pbs_experiments_avg_diffs_per_group.sh ..." 
	$< -b ./pbs_perf -u 1000000 -d "10000" -p $(PARAMDIR)/$(PRARM_FN_PREFIX) -e "$(DATADIR)/$(EST_FILENAME_PATTERN)" -g $(DIFF_AVGS) -i $(DATADIR)/$(LARGER_SETS) -o $@
	@chmod +x $@

scripts: $(BUILD)/pbs_experiments_diffs.sh $(BUILD)/pbs_experiments_vs_graphene_diffs.sh $(BUILD)/pbs_experiments_avg_diffs_per_group.sh
	@echo "Generate scripts for PBS ..."

params:
	@echo "Generating Parameters"
	(cd $(TOP) && ./parameter_calc.py)

perf: $(BUILD)/pbs_perf scripts params
	@echo "Benchmarking PBS ..."
	(cd $(BUILD) && ./pbs_experiments_diffs.sh)
	(cd $(BUILD) && ./pbs_experiments_vs_graphene_diffs.sh)
	(cd $(BUILD) && ./pbs_experiments_avg_diffs_per_group.sh)
	@echo "DONE!"

#
# This target runs a few experiments using the exact same configurations
# as we used before to verify that this version of codes (with relatively
# large modifications) can produce the same results and run at similar
# speed on the same machine
#
consistency_test: $(BUILD)/pbs_perf_py_seeds
	(cd $(BUILD) && ./pbs_perf_py_seeds -n 1000 -d 10 -s 0 -u 100000 -e $(DATAOLDDIR)/diff_estimates_with_tow_10_128_9012.txt -i $(DATAOLDDIR)/$(SETS) -r 1.38 -R 3 -p $(PARAMDIR)/params_r3.csv -g 5.0)
	(cd $(BUILD) && ./pbs_perf_py_seeds -n 1000 -d 10000 -s 18420 -u 100000 -e $(DATAOLDDIR)/diff_estimates_with_tow_10000_128_9012.txt -i $(DATAOLDDIR)/$(SETS) -r 1.38 -R 3 -p $(PARAMDIR)/params_r3.csv -g 5.0)

clean:
	$(RM) $(BUILD)

.PHONY: clean test perf script params