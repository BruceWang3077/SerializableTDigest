from typing import List
import json

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
    def __init__(self, compression=1000, unmerged_size=0, merged_size=0):
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
        for i, item in enumerate(tdigest.cumulative):
            print(i, ':', item);
        
        return tdigest

    @staticmethod
    def read_file(filename: str) -> str:
        """Reads the content of a file and returns it as a string."""
        with open(filename, 'r') as file:
            return file.read()
    
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

    def add(self, x, weight=1.0):
        """Adds a single value with an associated weight."""
        self.unprocessed.append(Centroid(x, weight))
        self.unprocessed_weight += weight
        if len(self.unprocessed) > self.max_unprocessed:
            self.process()

    def merge(self, other: 'TDigest'):
        """Merges another TDigest into this one."""
        self.unprocessed.extend(other.unprocessed)
        self.processed.extend(other.processed)
        self.processed_weight += other.processed_weight
        self.unprocessed_weight += other.unprocessed_weight
        self.process_if_necessary()

    def process_if_necessary(self):
        """Processes the centroids if the size exceeds the maximum allowed."""
        if len(self.processed) > self.max_processed or len(self.unprocessed) > self.max_unprocessed:
            self.process()

    def process(self):
        """Processes unprocessed centroids into processed centroids."""
        self.processed.extend(self.unprocessed)
        self.processed_weight += self.unprocessed_weight
        self.unprocessed.clear()
        self.unprocessed_weight = 0.0
        self.processed.sort(key=lambda c: c.mean)
        self.update_cumulative()

    def update_cumulative(self):
        """Updates cumulative weights for processed centroids."""
        n = len(self.processed)
        self.cumulative.clear()
        previous = 0.0
        for i in range(n):
            current = self.processed[i].weight
            half_current = current / 2.0
            self.cumulative.append(previous + half_current)
            previous += current
        self.cumulative.append(previous)


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

    def quantile_processed(self, q: float) -> float:
        """Calculates the quantile on processed centroids."""
        if q < 0 or q > 1:
            return float('nan')
        if not self.processed:
            return float('nan')
        elif len(self.processed) == 1:
            return self.processed[0].mean

        index = q * self.processed_weight
        if index <= self.processed[0].weight / 2.0:
            return self.min + 2.0 * index / self.processed[0].weight * (self.processed[0].mean - self.min)

        for i, cum in enumerate(self.cumulative):
            if cum >= index:
                prev_cum = self.cumulative[i - 1] if i > 0 else 0.0
                z1 = index - prev_cum
                z2 = cum - index
                return self.weighted_average(self.processed[i - 1].mean, z2, self.processed[i].mean, z1)

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
