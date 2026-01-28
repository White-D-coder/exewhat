import pandas as pd

file_path = "Copy of Unstop22 (2).xlsx"

try:
    df = pd.read_excel(file_path)
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nInfo:")
    print(df.info())
except Exception as e:
    print(f"Error reading file: {e}")
