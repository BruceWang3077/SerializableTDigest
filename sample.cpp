#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/text_iarchive.hpp>
#include <boost/serialization/vector.hpp>
#include <fstream>
#include <iostream>
#include "TDigest.h"
#include <random>
#include "glog/logging.h"
#include "gtest/gtest.h"


#include "TDigest.h"


#include <dirent.h>  // Include the correct header for directory operations

using namespace tdigest;

int write(std::string content, std::string file){

    std::ofstream outFile(file); // Specify your file name here

    // Check if the file is open
    if (outFile.is_open()) {
        outFile << content;
        outFile.close();
        std::cout << "Successfully written to the file."<< file << std::endl;
    } else {
        std::cerr << "Unable to open the file." << std::endl;
    }
    return 0;
}

int write_t(tdigest::TDigest& t, std::string file){
    std::ofstream outFile(file); // Specify your file name here
    int quantiles[] = {50, 90, 95, 99};

    // Check if the file is open
    if (outFile.is_open()) {
        for (int q : quantiles) {
            double quantile_value = t.quantile(q / 100.0);
            outFile << "Quantile " << q << "%: " << quantile_value << std::endl;
        }
        outFile.close();
        std::cout << "Successfully written to the file."<< file << std::endl;
    } else {
        std::cerr << "Unable to open the file." << std::endl;
    }
    return 0;
}
void process_folder_and_serialize(const std::string& input_folder_path, const std::string& output_folder_path) {
    //process all the csv files in the given folder, for each file, collect values using one tdigest and serialize it to the output folder with the corresponding name
    DIR* dir;
    struct dirent* entry;

    if ((dir = opendir(input_folder_path.c_str())) != nullptr) {
        while ((entry = readdir(dir)) != nullptr) {
            std::string file_name = entry->d_name;
            if (file_name.size() > 4 && file_name.substr(file_name.size() - 4) == ".csv") {
                std::string input_file_path = input_folder_path + "/" + file_name;
                std::ifstream input_file(input_file_path);
                if (!input_file.is_open()) {
                    std::cerr << "Unable to open file: " << input_file_path << std::endl;
                    continue;
                }

                // Create a TDigest and feed all data from the file
                tdigest::TDigest tdigest;
                std::string line;
                while (std::getline(input_file, line)) {
                    try {
                        double value = std::stod(line);
                        tdigest.add(value);
                    } catch (const std::invalid_argument& e) {
                        std::cerr << "Invalid value in file: " << input_file_path << " - " << line << std::endl;
                    }
                }
                input_file.close();

                // Serialize TDigest to JSON string
                std::string json_str = tdigest.serializeToJson();

                // Write JSON string to output file
                std::string base_name = file_name.substr(0, file_name.size() - 4); // Remove .csv suffix
                std::string output_file_path = output_folder_path + "/" + base_name + ".json";
                // write(json_str, output_file_path);

                //alternative approach
                tdigest.saveToFile(output_file_path);
            }
        }
        closedir(dir);
    } else {
        throw std::runtime_error("Unable to open directory: " + input_folder_path);
    }
}

tdigest::TDigest process_folder(const std::string& folder_path) {
    //process all the csv files in the given folder, then merge and return the final single tdigest
    
    std::vector<tdigest::TDigest> tdigests;

    DIR* dir;
    struct dirent* entry;
    if ((dir = opendir(folder_path.c_str())) != nullptr) {
        while ((entry = readdir(dir)) != nullptr) {
            std::string file_name = entry->d_name;
            if (file_name.size() > 4 && file_name.substr(file_name.size() - 4) == ".csv") {
                std::string file_path = folder_path + "/" + file_name;
                std::ifstream file(file_path);
                if (!file.is_open()) {
                    std::cerr << "Unable to open file: " << file_path << std::endl;
                    continue;
                }

                tdigest::TDigest tdigest;
                std::string line;
                while (std::getline(file, line)) {
                    std::stringstream ss(line);
                    std::string cell;
                    while (std::getline(ss, cell, ',')) {
                        try {
                            double value = std::stod(cell);
                            tdigest.add(value);
                        } catch (const std::invalid_argument& e) {
                            std::cerr << "Invalid value encountered in file: " << file_path << std::endl;
                        }
                    }
                }
                tdigests.push_back(std::move(tdigest));  // Use move semantics to avoid copy constructor issues
                file.close();
            }
        }
        closedir(dir);
    } else {
        throw std::runtime_error("Unable to open directory: " + folder_path);
    }

    if (tdigests.empty()) {
        throw std::runtime_error("No valid .csv files found in the folder");
    }

    if (tdigests.size() == 1) {
        return std::move(tdigests[0]);  // Return by moving to avoid deleted copy constructor
    }

    tdigest::TDigest merged_tdigest;
    for (auto& td : tdigests) {
        merged_tdigest.merge(&td);  // Pass by pointer to match merge function signature
    }

    return merged_tdigest;
}

int main(){
  google::InitGoogleLogging("testing::TDigestTest");

  tdigest::TDigest t_single = process_folder("./test_data/single");
  write_t(t_single, "./test_output/single_cpp.txt");

  tdigest::TDigest t_multiple = process_folder("./test_data/multiple");
  write_t(t_multiple, "./test_output/multiple_cpp.txt");

  process_folder_and_serialize("./test_data/multiple", "./test_output/serialized");


  // tdigest::TDigest digest(100);
  // std::uniform_real_distribution<> reals(0.0, 1.0);
  // std::random_device gen;
  // for (int i = 0; i < 100000; i++) {
  //   digest.add(reals(gen));
  // }
  // digest.compress();
  // double quantiles[4] = {0.5, 0.8, 0.9, 0.99};
  // std::string json = digest.serializeToJson();
  // write(json, "/tmp/tdigest.json");
  
  // tdigest::TDigest t2 = tdigest::TDigest::deserializeFromJson(json);

  // for(double i = 0; i < 100; i += 1){
  //   std::cout << i << "%: " << digest.quantile(i/100) << "  "<< t2.quantile(i/100)<< std::endl;
  // }
}




