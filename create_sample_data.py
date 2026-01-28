import pandas as pd
import os

# Sample data
data = {
    'Name': ['Test User 1', 'Test User 2'],
    'Phone': ['919876543210', '919876543211'], # Replace with real test numbers
    'Email': ['test1@example.com', 'test2@example.com'], # Replace with real test emails
    'Message': ['Hello! This is a test message with a community link: https://chat.whatsapp.com/xyz', 
                'Hi! Join our new community: https://chat.whatsapp.com/abc'],
    'Status': ['Pending', 'Pending'],
    'Email_Status': ['Pending', 'Pending']
}

df = pd.DataFrame(data)

# File path
file_path = '/Users/deeptanubhunia/Desktop/exewhat/data.xlsx'

# Save to Excel
df.to_excel(file_path, index=False)

print(f"Sample Excel file created at: {file_path}")
print("Please edit the 'Phone' and 'Email' columns with valid details before running app.py")
