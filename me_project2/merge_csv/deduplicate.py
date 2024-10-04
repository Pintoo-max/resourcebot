import pandas as pd

# Define the columns and their respective data types
dtype = {
    'IFSC': str,
    'URL': str,
    'BANK': str,
    'BRANCH': str,
    'CENTRE': str,
    'DISTRICT': str,
    'STATE': str,
    'ADDRESS': str,
    'CITY': str,
    'BANK_EMAIL': str,
    'BRANCH_TIMINGS': str,
    'CONTACT': str,
    'OFFICIAL_WEBSITE': str,
    'TOLL': str,
    'BRANCH_CODE': str,
    'MICR': str,
    'PINCODE': str,
    'TIMESTAMP': str,
}

# Read the merged CSV file with specified data types
merged = pd.read_csv('merged.csv', dtype=dtype, low_memory=False)

# Drop duplicates based on the IFSC column, keeping the first occurrence
deduplicated = merged.drop_duplicates(subset='IFSC', keep='first')

# Save the deduplicated DataFrame to a new CSV file
deduplicated.to_csv('deduplicated_merged.csv', index=False)

print(f"Total entries in deduplicated_merged.csv: {len(deduplicated)}")
