


# Serializable TDigest
This is a TDigest library in C++/Python with serialization support. The implementation is based on Derrick Burns' [tdigest](https://github.com/derrickburns/tdigest), which is a high performance tdigest implementation that supports add, merge, percentile operations.

The serialization feature utilizes JSON, supports serializing a C++/Python tdigest object to a string, and deserializing it into a Python object for further data analyze.

## C++ Tdigest Basic Illustration
In Derrick Burns' implementation, Glog is a dependency used to check the conditions, it needs to be initialized first

    google::InitGoogleLogging("testing::TDigestTest");

add values and query percentile

    //create
    tdigest::TDigest tdigest;

    //add value
    double value = 1.0;
    tdigest.add(value);

    //merge
    tdigest::TDigest tmp;
    tmp.add(0.2);
    tdigest.merge(tmp);

    //query
    std::cout << tdigest.quantile(0.90) << std::endl // query 90% percentile

    //serialize 
    std::string json_str = tdigest.serializeToJson();

To save a serialized tdigest more easily, in TDigest.h, there's a wrapper function
```void saveToFile(const std::string& filename)```

## Python Tdigest
Python implementation APIs are very similar and intuitive.

For deserialization, there are two options:

```def deserialize_file(file_path: str) -> 'TDigest':``` with a file input

or

```def deserialize(json_str: str) -> 'TDigest':``` with a string input

for the case that requires deserializing a bunch of files into a single tdigest, there's a wrapper function ```def merge_from_files_linear(file_paths: List[str]) -> 'TDigest':``` that does this.

## Some Tests and Running Illustrations

### to run ```sample.cpp```:
compile and build:

    python3 waf configure build 

to run

    ./build/sample_test




- what's in it:
    - ```int write_t(tdigest::TDigest& t, std::string file)``` this is a simulation of a single machine system, where multiple clients/threads collect data and merge into one final tdigest
    - ```void process_folder_and_serialize(const std::string& input_folder_path, const std::string& output_folder_path)``` this is a simulation of a distributed system where mulitple machines/datacenters collect data and serialize their tdigest objects respectively(one tdigest for each machine/datacenter), which could be collected on one machine and used for analysis after deserialization.
    - ```int write_t(tdigest::TDigest& t, std::string file)``` this is a helper function that writes certain percentiles data into a file

### TDigest_test.py

simply run the command

    python3 TDigest_test.py

- what's in it
    - ```def test_serialize_deserialize()``` this is a test for compression and serialization, to see if the serialize/deserialize process will affect the data
    - ```def process_folder(folder_path)``` same as ```process_folder``` in ```sample.cc```
    - ```def deserialize_tdigest_from_folder(folder_path)``` this is simulation test for the scenario that the python scripts need to collect the data from multiple machines/datacenters and merge them into one tdigest object for analysis
    - ```def heavy_test(batch)```this is a performance test to test the merge performance. ```batch``` is the number of tdigest to merge
    







