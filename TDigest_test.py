import random
import time
import os
from tdigest import TDigest 
import pandas as pd
import numpy as np


def deserialize_tdigest_from_folder(folder_path):
    tdigests = []
    
    # Read all JSON files in the folder and deserialize to TDigest objects
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            try:
                with open(file_path, 'r') as file:
                    json_str = file.read()
                    tdigest = TDigest.deserialize(json_str)
                    tdigests.append(tdigest)
            except Exception as e:
                print(f"Error reading or deserializing {file_name}: {e}")

    # Return the appropriate TDigest
    if not tdigests:
        raise ValueError("No valid JSON files found in the folder")
    
    if len(tdigests) == 1:
        return tdigests[0]
    
    # Merge all tdigests if there are multiple
    merged_tdigest = TDigest()
    for td in tdigests:
        merged_tdigest.merge(td)
    
    return merged_tdigest
def create_tdigest_from_folder(folder_path):
    tdigests = []
    
    # Read all data from CSV files in the folder and create a TDigest for each
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            try:
                data = pd.read_csv(file_path, header=None).squeeze().tolist()
                tdigest = TDigest(100)
                for value in data:
                    tdigest.add(value)
                tdigests.append(tdigest)
            except Exception as e:
                print(f"Error reading {file_name}: {e}")

    # Return the appropriate TDigest
    if not tdigests:
        raise ValueError("No valid CSV files found in the folder")
    
    if len(tdigests) == 1:
        return tdigests[0]
    
    # Merge all tdigests if there are multiple
    merged_tdigest = TDigest(100)
    for td in tdigests:
        merged_tdigest.merge(td)
    
    return merged_tdigest

def write_quantiles_to_file(tdigest, output_file_path):
    quantiles = [50, 90, 95, 99]
    with open(output_file_path, 'w') as output_file:
        for q in quantiles:
            value = tdigest.quantile(q / 100.0)
            output_file.write(f"Quantile {q}%: {value}\n")

def calculate_quantiles(folder_path, output_file_path):
    all_data = []
    
    # Read all data from CSV files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            try:
                data = pd.read_csv(file_path, header=None).squeeze().tolist()
                all_data.extend(data)
            except Exception as e:
                print(f"Error reading {file_name}: {e}")

    # Sort all the data
    all_data.sort()

    # Calculate quantiles
    quantiles = [50, 90, 95, 99]
    quantile_values = np.percentile(all_data, quantiles)

    # Write quantile values to the output file
    with open(output_file_path, 'w') as output_file:
        for q, value in zip(quantiles, quantile_values):
            output_file.write(f"Quantile {q}%: {value}\n")

def heavy_test(batch):
    def print_(t1):
        for i in range(100):
            print("i: ", i, " ", t1.percentile(i))
    # Create a directory for dumping serialized TDigest files
    dump_dir = "dump"
    os.makedirs(dump_dir, exist_ok=True)

    tdigest_list = []
    for i in range(batch):
        tdigest = TDigest(compression=100)
        for _ in range(10000):
            value = random.uniform(0, 1)
            tdigest.add(value)
        tdigest_list.append(tdigest)

    file_names = []
    for idx, tdigest in enumerate(tdigest_list):
        file_name = os.path.join(dump_dir, f"tdigest_{idx}.json")
        with open(file_name, 'w') as file:
            file.write(tdigest.serialize())
        file_names.append(file_name)

    # start_time = time.time()
    # merged_tdigest_multithreaded = TDigest.merge_from_files(file_names)
    # multithreaded_time = time.time() - start_time


    start_time = time.time()
    merged_tdigest_linear = TDigest.merge_from_files_linear(file_names)
    linear_time = time.time() - start_time

    print_(merged_tdigest_linear)

    print(f"Time taken for linear merge: {linear_time:.2f} seconds")

    # Clean up the serialized files
    # for file_name in file_names:
    #     os.remove(file_name)

    # # Remove the dump directory
    # os.rmdir(dump_dir)



def process_csv_files(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)  # Skip the first row (column names)
            print(df.columns)
            if 'All-Original' in df.columns:
                all_original_column = df['All-Original']  # Keep only the 'All-Original' column (with leading space)
                processed_df = pd.DataFrame(all_original_column)
                processed_file_path = os.path.join(folder_path, f"processed_{file_name}")
                processed_df.to_csv(processed_file_path, index=False, header=False)
            else:
                print(f"Column 'All-Original' not found in file: {file_name}")

# Example usage:
# process_csv_files('/path/to/your/folder')

    
def test_serialize_deserialize():
    """Static method to test serialization and deserialization of TDigest."""
    # 1. Create a TDigest with default parameters
    tdigest1 = TDigest()

    # 2. Put in 10000 real numbers uniformly distributed between 0 to 1
    for _ in range(1000000):
        value = random.uniform(0, 1)
        tdigest1.add(value)

    # 3. Serialize it to a file in ./tmp/
    os.makedirs("./tmp", exist_ok=True)
    serialized_str = tdigest1.serialize()
    file_path = "./tmp/tdigest.json"
    with open(file_path, 'w') as file:
        file.write(serialized_str)

    # 4. Deserialize it into another TDigest object
    with open(file_path, 'r') as file:
        deserialized_str = file.read()
    tdigest2 = TDigest.deserialize(deserialized_str)

    # 5. Print the percentile from 1 to 100 of both TDigest objects
    for i in range(0, 99):
        print(f"{i}% : {tdigest1.percentile(i)} {tdigest2.percentile(i)}")


if __name__ == "__main__":
    # test_serialize_deserialize()

    # calculate_quantiles("./test_data/multiple","./test_output/multiple_real.txt")
    # calculate_quantiles("./test_data/single","./test_output/single_real.txt")

    # write_quantiles_to_file(create_tdigest_from_folder("./test_data/multiple"), "./test_output/multiple_py.txt")
    # write_quantiles_to_file(create_tdigest_from_folder("./test_data/single"), "./test_output/single_py.txt")


    # write_quantiles_to_file(deserialize_tdigest_from_folder("./test_output/serialized"), './test_output/aws_simulate_py.txt')

    heavy_test(1000)
    # quantile_test()