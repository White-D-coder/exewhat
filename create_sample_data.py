import pandas as pd
import os

# Sample data
data = {
    'Name': ['Test User 1', 'Test User 2'],
    'Phone': ['919876543210', '919876543211'], # Replace with real test numbers
    'Message': ['Hello! This is a test message with a community link: https://chat.whatsapp.com/xyz', 
                'Hi! Join our new community: https://chat.whatsapp.com/abc'],
    'Status': ['Pending', 'Pending']
}

df = pd.DataFrame(data)

# File path
file_path = '/Users/deeptanubhunia/Desktop/exewhat/data.xlsx'

# Save to Excel
df.to_excel(file_path, index=False)

print(f"Sample Excel file created at: {file_path}")
print("Please edit the 'Phone' column with valid numbers before running main.py")
