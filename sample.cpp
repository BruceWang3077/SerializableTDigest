#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/text_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <fstream>
#include <iostream>
#include "TDigest.h"
#include <random>
#include "glog/logging.h"
#include "gtest/gtest.h"
// class MyClass {
// public:
//     int value;
//     std::string name;

//     MyClass() = default;  // Default constructor needed for deserialization

//     MyClass(int v, std::string n) : value(v), name(std::move(n)) {}

//     // Serialization function
//     template<class Archive>
//     void serialize(Archive &ar, const unsigned int version) {
//         ar & value;
//         ar & name;
//     }
// };

// void save_tdigest(const tdigest::TDigest& td, const std::string& filename) {
//   std::ofstream ofs(filename);
//   boost::archive::text_oarchive oa(ofs);
//   oa << td;
// }

// // Load function
// void load_tdigest(tdigest::TDigest& td, const std::string& filename) {
//   std::ifstream ifs(filename);
//   boost::archive::text_iarchive ia(ifs);
//   ia >> td;
// }
// void test_centroid_serialization() {
//     // Create a Centroid object
//     tdigest::Centroid c1(5.5, 10.0);
//     std::cout << "Original Centroid: mean = " << c1.mean() << ", weight = " << c1.weight() << std::endl;

//     // Serialize the Centroid object to a file
//     std::ofstream ofs("centroid_serialized.txt");
//     boost::archive::text_oarchive oa(ofs);
//     oa << c1;
//     ofs.close();

//     // Create another Centroid object for deserialization
//     tdigest::Centroid c2;

//     // Deserialize the Centroid object from the file
//     std::ifstream ifs("centroid_serialized.txt");
//     boost::archive::text_iarchive ia(ifs);
//     ia >> c2;
//     ifs.close();

//     // Verify that the deserialized data matches the original
//     std::cout << "Deserialized Centroid: mean = " << c2.mean() << ", weight = " << c2.weight() << std::endl;
//     assert(c1.mean() == c2.mean());
//     assert(c1.weight() == c2.weight());

//     std::cout << "Serialization test passed!" << std::endl;
// }
// int json(tdigest::TDigest& t){
//   std::string s = t.serializeToJson();
//   std::cout << s << std::endl;
//   return 0;
// }
int write(std::string content, std::string file){

    std::ofstream outFile(file); // Specify your file name here

    // Check if the file is open
    if (outFile.is_open()) {
        outFile << content;
        outFile.close();
        std::cout << "Successfully written to the file." << std::endl;
    } else {
        std::cerr << "Unable to open the file." << std::endl;
    }
    return 0;
}
int main(){
  google::InitGoogleLogging("testing::TDigestTest");
  tdigest::TDigest digest(100);
  std::uniform_real_distribution<> reals(0.0, 1.0);
  std::random_device gen;
  for (int i = 0; i < 100000; i++) {
    digest.add(reals(gen));
  }
  digest.compress();
  double quantiles[4] = {0.5, 0.8, 0.9, 0.99};
  std::string json = digest.serializeToJson();
  write(json, "tdigest.json");
  
  tdigest::TDigest t2 = tdigest::TDigest::deserializeFromJson(json);
  // Serialize (save to file)
  // save_tdigest(digest, "tdigest.txt");
  
  // for(int i = 0; i < sizeof(quantiles) / sizeof(quantiles[0]); i++){
  //   std::cout << digest.quantile(quantiles[i]) << std::endl;
  // }
  // std::cout << "serialization done" << std::endl;
  // tdigest::TDigest digest2;
  // load_tdigest(digest2, "tdigest.txt");
  for(double i = 0; i < 100; i += 1){
    std::cout << i << "%: " << digest.quantile(i/100) << "  "<< t2.quantile(i/100)<< std::endl;
  }
}

// int main() {
//     // test_centroid_serialization();
//     tdigest::Centroid c1(5.5, 10.0);
//     tdigest::Centroid c2(5.5, 10.0);
//     tdigest::Centroid c3(5.5, 10.0);
//     tdigest::Centroid c4(5.5, 10.0);
//     tdigest::Centroid c5(5.5, 10.0);
//     std::vector<tdigest::Centroid> vec;
//     vec.push_back(c1);
//     vec.push_back(c2);
//     vec.push_back(c3);
//     vec.push_back(c4);
//     vec.push_back(c5);
//     std::ofstream ofs("centroid_serialized.txt");
//     boost::archive::text_oarchive oa(ofs);
//     oa << vec;
//     ofs.close();


//     std::vector<tdigest::Centroid> vec2;
//     std::ifstream ifs("centroid_serialized.txt");
//     boost::archive::text_iarchive ia(ifs);
//     ia >> vec2;
//     ifs.close();
    
//     std::cout << "size" << vec2.size() << std::endl;
    
//     return 0;
// }


