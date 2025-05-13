from typing import List
import json
import concurrent.futures
import random
import os
import math
# Equivalent `Centroid` class in Python
class Centroid:
    def __init__(self, mean=0.0, weight=0.0):
        self.mean = mean
        self.weight = weight

    def add(self, other_centroid):
        """Merges another Centroid into this one."""
        assert other_centroid.weight > 0, "Weight must be positive"
        if self.weight != 0.0:
            self.weight += other_centroid.weight
            self.mean += other_centroid.weight * (other_centroid.mean - self.mean) / self.weight
        else:
            self.weight = other_centroid.weight
            self.mean = other_centroid.mean


class TDigest:
    def __init__(self, compression=100, unmerged_size=0, merged_size=0):
        self.compression = compression
        self.max_processed = self.processed_size(merged_size, compression)
        self.max_unprocessed = self.unprocessed_size(unmerged_size, compression)
        self.processed = []
        self.unprocessed = []
        self.processed_weight = 0.0
        self.unprocessed_weight = 0.0
        self.min = float("inf")
        self.max = float("-inf")
        self.cumulative = []

    @staticmethod
    def weight(centroids: List[Centroid]) -> float:
        """Calculates the total weight of the centroids."""
        return sum(centroid.weight for centroid in centroids)

    @staticmethod
    def processed_size(size: int, compression: float) -> int:
        """Computes the processed size based on compression."""
        return int(2 * compression) if size == 0 else size

    @staticmethod
    def unprocessed_size(size: int, compression: float) -> int:
        """Computes the unprocessed size based on compression."""
        return int(8 * compression) if size == 0 else size

    def print_self(self):
        print("compression: ", self.compression)
        print('processed: ', len(self.processed))
        print("unprocessed: ", len(self.unprocessed))
        print("processed weight: ", self.processed_weight)
        
    def add(self, x, weight=1.0):
        """Adds a single value with an associated weight."""
        self.unprocessed.append(Centroid(x, weight))
        self.unprocessed_weight += weight
        if len(self.unprocessed) > self.max_unprocessed:
            self.process()
    def merge(self, other: 'TDigest'):
        """Merges another TDigest into this one."""
        # Process unprocessed centroids in both digests before merging
        self.compress()
        other.compress()

        # Merge processed centroids from the other digest into this one
        combined_centroids = self.processed + other.processed
        combined_centroids.sort(key=lambda c: c.mean)

        self.processed = []
        self.processed_weight = 0.0
        self.unprocessed_weight = 0.0

        # Rebuild processed centroids with merged data
        self.processed.append(combined_centroids[0])
        w_so_far = combined_centroids[0].weight
        w_limit = self.weight(combined_centroids) * self.integrated_q(1.0)

        for i in range(1, len(combined_centroids)):
            centroid = combined_centroids[i]
            projected_w = w_so_far + centroid.weight
            if projected_w <= w_limit:
                w_so_far = projected_w
                self.processed[-1].add(centroid)
            else:
                k1 = self.integrated_location(w_so_far / self.weight(combined_centroids))
                w_limit = self.weight(combined_centroids) * self.integrated_q(k1 + 1.0)
                w_so_far += centroid.weight
                self.processed.append(centroid)

        # Update min, max, and cumulative weights
        self.min = min(self.min, other.min)
        self.max = max(self.max, other.max)
        self.processed_weight = self.weight(self.processed)
        self.update_cumulative()

    def process_if_necessary(self):
        """Processes the centroids if the size exceeds the maximum allowed."""
        if len(self.processed) > self.max_processed or len(self.unprocessed) > self.max_unprocessed:
            self.process()

    def process(self):
        """Processes unprocessed centroids into processed centroids."""
        # Sort unprocessed centroids by their mean
        self.unprocessed.sort(key=lambda c: c.mean)
        count = len(self.unprocessed)
        if count == 0: return
        # Merge unprocessed and processed centroids
        self.unprocessed.extend(self.processed)
        self.unprocessed.sort(key=lambda c: c.mean)

        # Clear processed and update weights
        self.processed_weight += self.unprocessed_weight
        self.unprocessed_weight = 0.0
        self.processed.clear()

        # Initialize processing variables
        self.processed.append(self.unprocessed[0])
        w_so_far = self.unprocessed[0].weight
        w_limit = self.processed_weight * self.integrated_q(1.0)

        for i in range(1, len(self.unprocessed)):
            centroid = self.unprocessed[i]
            projected_w = w_so_far + centroid.weight
            if projected_w <= w_limit:
                w_so_far = projected_w
                self.processed[-1].add(centroid)
            else:
                k1 = self.integrated_location(w_so_far / self.processed_weight)
                w_limit = self.processed_weight * self.integrated_q(k1 + 1.0)
                w_so_far += centroid.weight
                self.processed.append(centroid)

        # Clear unprocessed and update min/max
        self.unprocessed.clear()
        self.min = min(self.min, self.processed[0].mean)
        self.max = max(self.max, self.processed[-1].mean)
        self.update_cumulative()


    def integrated_q(self, k: float) -> float:
        return (math.sin(min(k, self.compression) * math.pi / self.compression - math.pi / 2) + 1) / 2

    def integrated_location(self, q: float) -> float:
        return self.compression * (math.asin(2.0 * q - 1.0) + math.pi / 2) / math.pi

    def update_cumulative(self):
        """Updates cumulative weights for processed centroids."""
        n = len(self.processed)
        self.cumulative.clear()
        self.cumulative = [0.0] * (n + 1)
        previous = 0.0
        for i in range(n):
            current = self.processed[i].weight
            half_current = current / 2.0
            self.cumulative[i] = previous + half_current
            previous += current
        self.cumulative[n] = previous

    def cdf(self, x: float) -> float:
        """Calculates the cumulative distribution function (CDF) for a value x."""
        if len(self.unprocessed) > 0:
            self.process()
        return self.cdf_processed(x)

    def cdf_processed(self, x: float) -> float:
        """Calculates the CDF on processed centroids."""
        if not self.processed:
            return 0.0
        elif len(self.processed) == 1:
            return 1.0 if x >= self.max else 0.0 if x < self.min else 0.5
        if x < self.min:
            return 0.0
        if x >= self.max:
            return 1.0

        # Approximate position in the cumulative distribution
        weight_sum = 0.0
        for i, centroid in enumerate(self.processed):
            if centroid.mean >= x:
                if i == 0:
                    return 0.0
                prev = self.processed[i - 1]
                pos = (x - prev.mean) / (centroid.mean - prev.mean)
                weight_sum += pos * prev.weight
                break
            weight_sum += centroid.weight
        return weight_sum / self.processed_weight
        
    def percentile(self, q):
        return self.quantile(q/100)
        
    def quantile(self, q: float) -> float:
        """Calculates the quantile value for a given quantile q."""
        if len(self.unprocessed) > 0:
            self.process()
        return self.quantile_processed(q)

    # def quantile_processed(self, q: float) -> float:
    #     """Calculates the quantile on processed centroids."""
    #     if q < 0 or q > 1:
    #         return float('nan')
    #     if not self.processed:
    #         return float('nan')
    #     elif len(self.processed) == 1:
    #         return self.processed[0].mean

    #     index = q * self.processed_weight
    #     print("index: ", index)
    #     if index <= self.processed[0].weight / 2.0:
    #         return self.min + 2.0 * index / self.processed[0].weight * (self.processed[0].mean - self.min)

    #     for i, cum in enumerate(self.cumulative):
    #         if cum >= index:
    #             prev_cum = self.cumulative[i - 1] if i > 0 else 0.0
    #             z1 = index - prev_cum
    #             z2 = cum - index
    #             print("Q: i : ", i, " z1: ", z1, " z2: ", z2, "(i-1) mean: ", self.processed[i - 1].mean, " i mean: ", self.processed[i].mean)
    #             return self.weighted_average(self.processed[i - 1].mean, z2, self.processed[i].mean, z1)

    #     return self.max
    
    def quantile_processed(self, q: float) -> float:
        """Calculates the quantile on processed centroids, matching C++ behavior."""
        if q < 0 or q > 1:
            return float('nan')
        if not self.processed:
            return float('nan')
        elif len(self.processed) == 1:
            return self.processed[0].mean

        index = q * self.processed_weight
        n = len(self.processed)


        # Handle first boundary: interpolate between min and first centroid
        if index <= self.processed[0].weight / 2.0:
            return self.min + 2.0 * index / self.processed[0].weight * (self.processed[0].mean - self.min)

        # Handle middle cases: interpolate between consecutive centroids
        for i in range(1, n):
            if self.cumulative[i] >= index:
                prev_cum = self.cumulative[i - 1]
                cum = self.cumulative[i]
                z1 = index - prev_cum
                z2 = cum - index
                # print("Q_1: i : ", i, " z1: ", z1, " z2: ", z2, "(i-1) mean: ", self.processed[i - 1].mean, " i mean: ", self.processed[i].mean)
                return self.weighted_average(self.processed[i - 1].mean, z2, self.processed[i].mean, z1)

        # Handle last boundary: interpolate between last centroid and max
        if index <= self.processed_weight:
            z1 = index - self.cumulative[n - 1]
            z2 = self.processed_weight - index
            return self.weighted_average(self.processed[n - 1].mean, z2, self.max, z1)

        return self.max

    @staticmethod
    def weighted_average(a: float, weight_a: float, b: float, weight_b: float) -> float:
        """Calculates a weighted average of two values."""
        return (a * weight_a + b * weight_b) / (weight_a + weight_b)

    def compress(self):
        """Compresses the t-digest by processing unprocessed centroids."""
        self.process()

    def compression_value(self) -> float:
        """Returns the compression value."""
        return self.compression

    def serialize(self) -> str:
        """Serializes the TDigest to a JSON string, ensuring the unprocessed centroids are empty."""
        self.compress()
        return json.dumps({
            "compression": self.compression,
            "maxProcessed": self.max_processed,
            "maxUnprocessed": self.max_unprocessed,
            "min": self.min,
            "max": self.max,
            "processedWeight": self.processed_weight,
            "unprocessedWeight": self.unprocessed_weight,
            "processed": [
                {"mean": centroid.mean, "weight": centroid.weight}
                for centroid in self.processed
            ]
        })

    @staticmethod
    def deserialize(json_str: str) -> 'TDigest':
        """Deserializes a TDigest from a JSON string."""
        data = json.loads(json_str)

        # Create an instance of TDigest
        tdigest = TDigest(
            compression=float(data["compression"]),
            merged_size=float(data["maxProcessed"]),
            unmerged_size=float(data["maxUnprocessed"])
        )

        # Set basic attributes
        tdigest.min = float(data["min"])
        tdigest.max = float(data["max"])
        tdigest.processed_weight = float(data["processedWeight"])
        tdigest.unprocessed_weight = float(data["unprocessedWeight"])
    
        # Deserialize `processed` centroids
        tdigest.processed = [
            Centroid(mean=float(centroid["mean"]), weight=float(centroid["weight"]))
            for centroid in data["processed"]
        ]

        tdigest.update_cumulative()
        
        return tdigest
    @staticmethod
    def deserialize_file(file_path: str) -> 'TDigest':
        json_str = TDigest.read_file(file_path)
        return TDigest.deserialize(json_str)
    
    
    @staticmethod
    def read_file(filename: str) -> str:
        """Reads the content of a file and returns it as a string."""
        with open(filename, 'r') as file:
            return file.read()

    @staticmethod
    def merge_from_files(file_paths: List[str]) -> 'TDigest':
        """Merges TDigest objects from a list of JSON file paths using multi-threading for efficiency.
        TODO: seems the current code doesn't improve the performance
        """


        with concurrent.futures.ThreadPoolExecutor() as executor:
            tdigests = list(executor.map(deserialize_file, file_paths))

        while len(tdigests) > 1:
            # Perform merging in parallel
            with concurrent.futures.ThreadPoolExecutor() as executor:
                merged_tdigests = list(executor.map(
                    lambda pair: pair[0].merge(pair[1]) or pair[0],
                    zip(tdigests[::2], tdigests[1::2])
                ))

            # If there's an odd digest left, append it without merging
            if len(tdigests) % 2 == 1:
                merged_tdigests.append(tdigests[-1])

            tdigests = merged_tdigests

        return tdigests[0]
    
    @staticmethod
    def merge_from_files_linear(file_paths: List[str]) -> 'TDigest':
        """Merges TDigest objects from a list of JSON file paths."""
        merged_tdigest = TDigest()
        for file_path in file_paths:
            json_str = TDigest.read_file(file_path)
            tdigest = TDigest.deserialize(json_str)
            merged_tdigest.merge(tdigest)
        return merged_tdigest



