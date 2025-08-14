CXX = g++
RM = rm -rf

CXXFLAGS = -O3 -Wall -std=c++11
LDFLAGS = -lxxhash

TARGET = tow_estimator

all: $(TARGET)

$(TARGET): tow_estimator.cpp
	$(CXX) $(CXXFLAGS) $< $(LDFLAGS) -o $@


clean:
	$(RM) $(TARGET) *.o
