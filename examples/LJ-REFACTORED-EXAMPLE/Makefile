# Makefile for PairLJCut Test Harness
# Supports both standard and HLS modes

# Compiler
CXX = g++

# Target executables
TARGET_STD = harness.exe
TARGET_HLS = harness_hls.exe

# Source files
SRCS = main.cpp bottleneck.cpp
OBJS_STD = main.o bottleneck.o
OBJS_HLS = main_hls.o bottleneck_hls.o

# Standard mode flags
CXXFLAGS_STD = -O3 -Wall -std=c++11 -g

# HLS mode flags (with HLS defined)
CXXFLAGS_HLS = -O3 -Wall -std=c++11 -g -DHLS

# Default target: build standard mode
all: $(TARGET_STD)

# Build HLS mode
hls: $(TARGET_HLS)

# Standard mode compilation
$(TARGET_STD): $(OBJS_STD)
	$(CXX) $(CXXFLAGS_STD) -o $(TARGET_STD) $(OBJS_STD)

main.o: main.cpp bottleneck.h
	$(CXX) $(CXXFLAGS_STD) -c main.cpp -o main.o

bottleneck.o: bottleneck.cpp bottleneck.h
	$(CXX) $(CXXFLAGS_STD) -c bottleneck.cpp -o bottleneck.o

# HLS mode compilation
$(TARGET_HLS): $(OBJS_HLS)
	$(CXX) $(CXXFLAGS_HLS) -o $(TARGET_HLS) $(OBJS_HLS)

main_hls.o: main.cpp bottleneck.h
	$(CXX) $(CXXFLAGS_HLS) -c main.cpp -o main_hls.o

bottleneck_hls.o: bottleneck.cpp bottleneck.h
	$(CXX) $(CXXFLAGS_HLS) -c bottleneck.cpp -o bottleneck_hls.o

# Run standard mode
run: $(TARGET_STD)
	ulimit -s unlimited && timeout 600 ./$(TARGET_STD)

# Run HLS mode
run-hls: $(TARGET_HLS)
	ulimit -s unlimited && timeout 600 ./$(TARGET_HLS)

# Clean build artifacts
clean:
	rm -f $(OBJS_STD) $(OBJS_HLS) $(TARGET_STD) $(TARGET_HLS)

# Clean everything including snapshots (use with caution)
clean-all: clean
	rm -f *.snapshot

.PHONY: all hls run run-hls clean clean-all