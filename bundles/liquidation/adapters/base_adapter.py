from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """
    Abstract Base Class for protocol-specific liquidation adapters.
    """
    
    @abstractmethod
    def fetch_raw_data(self):
        """
        Fetches raw data from the protocol source (e.g., API, Subgraph, RPC).
        """
        pass

    @abstractmethod
    def normalize(self, raw_data):
        """
        Transforms raw protocol data into the normalized schema.
        """
        pass

    def get_records(self):
        """
        Orchestrates fetch and normalization with error handling.
        """
        raw = self.fetch_raw_data()
        records = []
        for item in raw:
            try:
                normalized = self.normalize(item)
                if normalized:
                    records.append(normalized)
            except Exception as e:
                print(f"Warning: Failed to normalize record in {self.__class__.__name__}: {e}")
        return records
