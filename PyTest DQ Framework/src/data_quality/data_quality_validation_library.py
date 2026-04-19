import pandas as pd


class DataQualityLibrary:

    @staticmethod
    def check_duplicates(df, column_names=None):
        if column_names:
            duplicates = df.duplicated(subset=column_names)
        else:
            duplicates = df.duplicated()
        assert not duplicates.any(), f"Duplicates found:\n{df[duplicates]}"

    @staticmethod
    def check_count(df1, df2):
        assert len(df1) == len(df2), f"Row count mismatch: source={len(df1)}, target={len(df2)}"

    @staticmethod
    def check_data_completeness(df1, df2):
        assert len(df1) == len(df2), f"Data completeness check failed: source={len(df1)}, target={len(df2)}"

    @staticmethod
    def check_dataset_is_not_empty(df):
        assert not df.empty, "Dataset is empty!"

    @staticmethod
    def check_not_null_values(df, column_names=None):
        if column_names:
            for col in column_names:
                assert df[col].notna().all(), f"Null values found in column: {col}"
        else:
            assert df.notna().all().all(), "Null values found in dataset"