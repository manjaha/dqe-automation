import pandas as pd
import os


class ParquetReader:
    def process(self, path: str, include_subfolders: bool = False) -> pd.DataFrame:
        if include_subfolders:
            dfs = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.parquet'):
                        full_path = os.path.join(root, file)
                        dfs.append(pd.read_parquet(full_path))
            if dfs:
                return pd.concat(dfs, ignore_index=True)
            else:
                return pd.DataFrame()
        else:
            return pd.read_parquet(path)