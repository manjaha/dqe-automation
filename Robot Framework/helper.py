import pandas as pd
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement


def read_html_table_to_dataframe(table_element: WebElement) -> pd.DataFrame:
    """
    Read Plotly SVG table element and convert to pandas DataFrame.
    
    Args:
        table_element: Selenium WebElement representing the Plotly table
        
    Returns:
        pd.DataFrame with table data
    """
    # For Plotly tables, we need to extract data from SVG elements
    from selenium.webdriver.common.by import By
    
    # Find all columns
    columns = table_element.find_elements(By.CLASS_NAME, "y-column")
    
    headers = []
    all_data = []
    
    for column in columns:
        # Get column header
        header = column.find_element(By.ID, "header").text.strip()
        headers.append(header)
        
        # Get parent cell elements
        parent_cells = column.find_elements(By.CSS_SELECTOR, "g.column-cell")
        
        # Extract cells with their Y positions
        cells_with_position = []
        for parent in parent_cells:
            transform = parent.get_attribute("transform")
            if "translate" in transform:
                y_str = transform.split(",")[1].replace(")", "").strip()
                y_pos = float(y_str)
                
                try:
                    text_elem = parent.find_element(By.CLASS_NAME, "cell-text")
                    text = text_elem.text.strip()
                    
                    if text and text != header:
                        cells_with_position.append((y_pos, text))
                except:
                    pass
        
        # Sort by Y position
        cells_with_position.sort(key=lambda x: x[0])
        column_data = [text for y, text in cells_with_position]
        all_data.append(column_data)
    
    # Transpose columns to rows
    num_rows = len(all_data[0])
    rows = [[all_data[col][i] for col in range(len(all_data))] 
            for i in range(num_rows)]
    
    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)
    
    # Convert date column
    if 'Visit Date' in df.columns:
        df['Visit Date'] = pd.to_datetime(df['Visit Date']).dt.strftime('%Y-%m-%d')
    
    # Convert numeric columns
    if 'Average Time Spent' in df.columns:
        df['Average Time Spent'] = pd.to_numeric(df['Average Time Spent'], errors='coerce')
    
    # Sort for consistent comparison
    df = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    
    return df


def read_parquet_data(parquet_folder: str, filter_date: str = None) -> pd.DataFrame:
    """
    Read partitioned Parquet dataset with optional date filtering.
    
    Args:
        parquet_folder: Path to the Parquet dataset folder
        filter_date: Optional date filter in YYYY-MM-DD format (filters for last 7 days from this date)
        
    Returns:
        pd.DataFrame with Parquet data
    """
    parquet_path = Path(parquet_folder)
    
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet folder not found: {parquet_folder}")
    
    # Read all parquet files
    df = pd.read_parquet(parquet_path)
    
    # Select only needed columns (exclude partition_date)
    df = df[['facility_type', 'visit_date', 'avg_time_spent']]
    
    # Apply date filter - get last week of data
    if not filter_date:
        # If no filter provided, use the max date in the dataset
        max_date = pd.to_datetime(df['visit_date'].max())
    else:
        max_date = pd.to_datetime(filter_date)
    
    # Filter for last 7 days
    start_date = max_date - pd.Timedelta(days=6)  # 7 days including end date
    df = df[df['visit_date'] >= start_date]
    df = df[df['visit_date'] <= max_date]
    
    # Rename columns to match HTML table format
    df = df.rename(columns={
        'facility_type': 'Facility Type',
        'visit_date': 'Visit Date',
        'avg_time_spent': 'Average Time Spent'
    })
    
    # Convert date to string format for comparison
    df['Visit Date'] = pd.to_datetime(df['Visit Date']).dt.strftime('%Y-%m-%d')
    
    # Convert numeric columns
    df['Average Time Spent'] = pd.to_numeric(df['Average Time Spent'], errors='coerce')
    
    # Sort by all columns for consistent comparison
    df = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    
    return df


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> dict:
    """
    Compare two DataFrames for exact match.
    
    Args:
        df1: First DataFrame (HTML table)
        df2: Second DataFrame (Parquet data)
        
    Returns:
        dict with 'match' (bool) and 'differences' (str)
    """
    result = {
        'match': False,
        'differences': ''
    }
    
    # Check if shapes match
    if df1.shape != df2.shape:
        result['differences'] = f"Shape mismatch: HTML has {df1.shape[0]} rows × {df1.shape[1]} cols, Parquet has {df2.shape[0]} rows × {df2.shape[1]} cols"
        return result
    
    # Check if columns match
    if not df1.columns.equals(df2.columns):
        result['differences'] = f"Column mismatch:\nHTML columns: {list(df1.columns)}\nParquet columns: {list(df2.columns)}"
        return result
    
    # Compare values
    comparison = df1.compare(df2)
    
    if comparison.empty:
        result['match'] = True
        result['differences'] = 'DataFrames match exactly!'
        return result
    
    # Build detailed difference report
    diff_report = ["DataFrames do not match. Differences found:\n"]
    
    for idx in comparison.index:
        diff_report.append(f"\nRow {idx}:")
        for col in comparison.columns.levels[0]:
            if col in comparison.columns:
                html_val = comparison.loc[idx, (col, 'self')] if (col, 'self') in comparison.columns else None
                parquet_val = comparison.loc[idx, (col, 'other')] if (col, 'other') in comparison.columns else None
                if pd.notna(html_val) or pd.notna(parquet_val):
                    diff_report.append(f"  {col}: HTML={html_val}, Parquet={parquet_val}")
    
    result['differences'] = '\n'.join(diff_report)
    return result