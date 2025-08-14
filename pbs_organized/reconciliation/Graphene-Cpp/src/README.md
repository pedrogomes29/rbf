# C++ Implementation for Graphene (Protocol I)

We implement (more precisely, translate) the Graphene (Protocol I) in C++. We have to say that the original Python 
codes (one critical data structure, called [Invertible Bloom Lookup Table (IBLT)](https://github.com/umass-forensics/IBLT-optimization), is Python-wrapped C++ implementation)  kindly shared by the authors of the Graphene paper is good enough. Hence, in one of our recent papers, we use the Python codes directly. However, one reviewer suggested us to compare with Graphene that is implmented purely in C++ (because our algorithms are implemented in C++). So we started this project.

We may also translate the more complex version of Graphene, such as Protocol II, in the future.

## What is [Graphene](https://dl.acm.org/doi/10.1145/3341302.3342082)

Here, we quote the description of the authors of Graphene. 

> a method and protocol for interactive set reconciliation among peers in blockchains and related distributed systems. Through the novel combination of a Bloom filter and an Invertible Bloom Lookup Table (IBLT), Graphene uses a fraction of the network bandwidth used by deployed work for one- and two-way synchronization. 

For more details about Graphene, please refer to:
A. Pinar Ozisik, Gavin Andresen, Brian N. Levine, Darren Tapp, George Bissias, and Sunny Katkuri. 2019. [Graphene: efficient interactive set reconciliation applied to blockchain propagation](https://web.cs.umass.edu/publication/docs/2019/UM-CS-2019-001.pdf). In Proceedings of the ACM Special Interest Group on Data Communication (SIGCOMM ’19). Association for Computing Machinery, New York, NY, USA, 303–317. DOI:https://doi.org/10.1145/3341302.3342082
  
## Code Structure

+ [`./search\_params.h`](./search_params.h): the C++ implementation of the parameter optimzation predocures described in the Graphene paper. 
+ [`./graphene\_protocol_I.cpp`](./graphene_protocol_I.cpp): the C++ implementation for Graphene protocol I.
+ [`./test.cpp`](./test.cpp): A simple test for our implementation of Graphene protocol I.
+ [`./search\_params\_wrapper.cpp`](./search_params_wrapper.cpp): A Python wrapper for `search_params.h` (for testing and python wrapper learning purpose)
+ [`./bloom\_filter`](./bloom_filter): the 3rd-party C++ implementation for the standard Bloom filter. For more details regarding this implementaion, please refer to [its Github repository](https://github.com/ArashPartow/bloom).
+ [`./benchmark](./benchmark): Some benchmarks of speed, space used, and false positive rate for three different Bloom filter implementation. 

## Why Choose THAT Bloom Filter Implementation

We note that there are many open-source C/C++ implementations for Bloom filters. However, only few of them can be 
directly used in Graphene, because many of those implementations are not for the standard Bloom filter or they are highly coupled with other unrelated parts. We only found two GOOD implementations: [**C++ Bloom Filter Library**](https://github.com/ArashPartow/bloom) by Arash Partow and [libbloom](https://github.com/jvirkki/libbloom) by Jyri J. Virkki. We used the former since it has higher efficiency. More details can be found in [benchmark](./benchmark).

## Build

This implementation depends on [IBLT-optimization](https://github.com/umass-forensics/IBLT-optimization). Please 
clone it into the parent folder of the one I am located in.

```bash
# Assume you are currently in the same folder as me (README.md)
cd ..
git clone https://github.com/umass-forensics/IBLT-optimization
```

Then, you can can build the code for Graphene (Protocol I) ([`./graphene\_protocol_I.cpp`](./graphene_protocol_I.cpp))
```bash
make [graphene]
# Here `graphene` is optional
```


To run the tests:
```bash
make test
```

To run the benchmarks, please refer to [benchmark](./benchmark).


## Full Duplications

### Original (in Python) 
Results from `python3 ./graphene_original.py`, i.e., running the original Python version, to make sure all conditions are the same we have changed their bloom filter to [our Python wrapped open bloom filter](./bloom_filter) 
```bash
Running 10 trials for parameter combination: multiple of blk 0 blk size 9990 CB bound 0.004167
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
a = 24, fpr_sender = 0.99980002, iblt_rows_first = 54
communication = 795.0, Observed false positives = 10, succeed = True
Running 10 trials for parameter combination: multiple of blk 0 blk size 9900 CB bound 0.004167
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 98, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 97, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 99, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 97, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 97, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 97, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 98, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 96, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 97, succeed = True
a = 133, fpr_sender = 0.9746002539999999, iblt_rows_first = 200
communication = 2737.0, Observed false positives = 98, succeed = True
Running 10 trials for parameter combination: multiple of blk 0 blk size 9000 CB bound 0.004167
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 106, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 123, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 125, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 116, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 122, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 130, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 125, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 111, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 128, succeed = True
a = 160, fpr_sender = 0.12060087940000001, iblt_rows_first = 236
communication = 7786.0, Observed false positives = 120, succeed = True
```

### Our Translation (in C++)

```bash
$ make grahene_test
Test Graphene
chmod +x ./grahene
./grahene -n 10 -d 10 -s 0 -u 10000 -i ../experiment1/test_sets_10000_9990.txt
All results will be stored in the folder result_2782758200
#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,fpr_cal,fpr_real,bf_size,iblt_size
Observed false positives: 10
1,1,795.000000,1,11301.557000,12765.410000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
2,1,795.000000000,1,4419.456000000,3465.512000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
3,1,795.000000000,1,3482.880000000,2898.407000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
4,1,795.000000000,1,3238.829000000,2416.100000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
5,1,795.000000000,1,3010.315000000,2447.435000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
6,1,795.000000000,1,2750.597000000,2398.125000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
7,1,795.000000000,1,2813.712000000,2799.820000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
8,1,795.000000000,1,2823.465000000,2469.827000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
9,1,795.000000000,1,3130.865000000,2432.040000000,0.999800020,0.999797050,147.000000000,648.000000000
Observed false positives: 10
10,1,795.000000000,1,2748.132000000,2411.038000000,0.999800020,0.999797050,147.000000000,648.000000000
Total failures: 0
Simulation DONE!

./grahene -n 10 -d 100 -s 0 -u 10000 -i ../experiment1/test_sets_10000_9900.txt
All results will be stored in the folder result_244049826
#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,fpr_cal,fpr_real,bf_size,iblt_size
Observed false positives: 98
1,1,2737.000000,1,2835.308000,1792.536000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 97
2,1,2737.000000000,1,2178.815000000,1724.868000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 99
3,1,2737.000000000,1,2012.232000000,1780.215000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 97
4,1,2737.000000000,1,1978.108000000,1807.751000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 97
5,1,2737.000000000,1,1998.084000000,1770.896000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 97
6,1,2737.000000000,1,2027.938000000,1745.980000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 98
7,1,2737.000000000,1,1993.022000000,1729.213000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 96
8,1,2737.000000000,1,2031.411000000,1716.606000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 97
9,1,2737.000000000,1,2011.111000000,1688.459000000,0.974600254,0.974616474,337.000000000,2400.000000000
Observed false positives: 98
10,1,2737.000000000,1,1977.702000000,1886.459000000,0.974600254,0.974616474,337.000000000,2400.000000000
Total failures: 0
Simulation DONE!

./grahene -n 10 -d 1000 -s 0 -u 10000 -i ../experiment1/test_sets_10000_9000.txt
All results will be stored in the folder result_2595254856
#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,fpr_cal,fpr_real,bf_size,iblt_size
Observed false positives: 106
1,1,7786.000000,1,2709.459000,1811.183000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 123
2,1,7786.000000000,1,1954.439000000,1764.069000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 125
3,1,7786.000000000,1,2024.875000000,1737.575000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 116
4,1,7786.000000000,1,1997.182000000,1782.598000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 122
5,1,7786.000000000,1,1991.613000000,1733.834000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 130
6,1,7786.000000000,1,1985.264000000,1756.136000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 125
7,1,7786.000000000,1,1944.279000000,1740.589000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 111
8,1,7786.000000000,1,1994.022000000,1784.237000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 128
9,1,7786.000000000,1,2298.998000000,1902.331000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Observed false positives: 120
10,1,7786.000000000,1,1967.715000000,1730.698000000,0.120600879,0.120592347,4954.000000000,2832.000000000
Total failures: 0
Simulation DONE!

Test completed
```

## Authors

+ Ziheng Liu
+ Long Gong