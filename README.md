# Serene Benchmark

The Serene Benchmark project provides a common framework to evaluate different approaches for schema matching and mapping.
Currently, the framework supports evaluation of three approaches for semantic labeling of relational data sources.


### Prerequisites


To run evaluation benchmark,

1. The server for [Karma DSL](https://github.com/NICTA/iswc-2016-semantic-labeling) needs to be installed and started.
2. The server for [Serene](https://github.com/NICTA/serene) needs to be started.
Currently it is in a proprietary state, but an executable can be obtained upon request.
3. Neural nets: tensorflow and keras python packages.
4. [Serene Python client](https://github.com/NICTA/serene-python-client) should be installed.
Currently it is in a proprietary state, but a python egg file can be obtained upon request.

Decompress sources and labels in the data folder.

### How to test
Nose unittests needs to be installed. To run the tests:
```
nosetests
```

### Run
There are three different approaches for semantic typing which can be currently evaluated in this project:

1. DSL: domain-independent semantic labeller
2. DINT: relational data integrator
3. NNet: deep neural nets MLP and CNN.
 Additionally, there is an implementation of a random forest using scikit.

For NNetModel, allowed model types are: 'cnn@charseq' (CNN on character sequences), 'mlp@charfreq' (MLP on character freqs + entropy), 'rf@charfreq' (RF on character freqs + entropy)
'rf@charfreq' uses scikit implementation of random forests while DINT uses Spark mllib.

DINT feature configuration is explained [here](http://github.com/NICTA/serene-benchmark/blob/experimental/doc/features.txt),
and resampling strategy [here](http://github.com/NICTA/serene-benchmark/blob/experimental/doc/resampling-strategy).

DSL can be run in two modes: "normal" when labeled data is used only from one domain or "enhanced" when labeled from other domains is used.


To install the package 'serene-benchmark', run
```
python setup.py install
```

[benchmark.py](https://github.com/NICTA/serene-benchmark/blob/experimental/serene_benchmark/benchmark.py) provides a running example of two experiments to evaluate different approaches for semantic labeling.
