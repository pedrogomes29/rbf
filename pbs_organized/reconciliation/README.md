# Reconciliation Algorithms

## Supported Algorithms

+ [D.Digest](https://dl.acm.org/doi/abs/10.1145/2043164.2018462?casa_token=c5YcT1VUJ9kAAAAA:cDmtII6znlJkRtkXnJUUU1Iu0SAdi7_dfgqzt5H-MYb7UClzxVJ1DwHbSrOnLP8X_IRUSqqVoD1Z-A)
+ [PinSketch](https://web.cs.ucla.edu/~rafail/PUBLIC/89.pdf)
+ [Graphene](https://dl.acm.org/doi/10.1145/3341302.3342082)
+ [PBS](https://arxiv.org/pdf/2007.14569.pdf)

## Install Dependencies

Please refer to [root README](../README.md).

## Compile 

```bash
make
```

## Usage 

Please do not foget to add the library path (default: `/usr/local/lib`) to the environment variable `LD_LIBRARY_PATH` before running.

```bash
make perf
```



