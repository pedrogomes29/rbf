CXX = g++
RM = gio trash -f
MKDIR = mkdir -p

CXXFLAGS = -O3 -Wall -std=c++11 -I$(SRCDIR) -I$(IBLTDIR) -I$(BFDIR)

TOP := $(shell /bin/pwd)

BUILD = $(TOP)/build
SRCDIR = $(TOP)/src
IBLTDIR = $(TOP)/IBLT-optimization
BFDIR = $(TOP)/src/bloom_filter
DATAOLDDIR = ../../test-sets/100000-1000
DATADIR = ../../test-sets/1000000-1000
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

TARGET = $(BUILD)/graphene_perf

all: $(TARGET)

$(BUILD)/graphene_perf: $(SRCDIR)/graphene.cpp $(IBLTDIR)/iblt.cpp $(IBLTDIR)/utilstrencodings.cpp $(IBLTDIR)/murmurhash3.cpp
	@$(MKDIR) $(BUILD)
	$(CXX) $^ $(CXXFLAGS) -o $@

$(BUILD)/graphene_experiments_diffs.sh: $(TOP)/cli_utils.py $(BUILD)/graphene_perf
	@$(MKDIR) $(BUILD)
	@echo "Generating bash script graphene_experiments_diffs.sh ..."
	$< -b ./graphene_perf -u 1000000 -d $(TEST_DIFFS) -i $(DATADIR)/$(LARGER_SETS) -o $@
	@chmod +x $@

scripts: $(BUILD)/graphene_experiments_diffs.sh
	@echo "Generating scripts for Graphene ..."

perf: $(BUILD)/graphene_experiments_diffs.sh
	@echo "Benchmarking Graphene ..."
	(cd $(BUILD) && ./graphene_experiments_diffs.sh)
	@echo "DONE!"
	
clean:
	$(RM) $(BUILD)






