import pandas as pd
from tqdm import tqdm

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

# Read the CSV files with specified data types
A = pd.read_csv('A.csv', dtype=dtype, low_memory=False)
B = pd.read_csv('B.csv', dtype=dtype, low_memory=False)

# Define the columns to be populated from B.csv
b_columns = ['IFSC', 'URL', 'BANK', 'BRANCH', 'CENTRE', 'DISTRICT', 'STATE', 'ADDRESS', 'CITY']

# Fill missing columns in B.csv with empty strings if they are not present
for column in A.columns:
    if column not in B.columns:
        B[column] = ''

# Create a dictionary from B for quick lookup
b_dict = B.set_index('IFSC').T.to_dict()

# Merge entries from B into A with progress tracking
for index, row in tqdm(A.iterrows(), total=A.shape[0], desc="Merging entries from B into A", unit=" rows"):
    if row['IFSC'] in b_dict:
        for column in A.columns:
            if pd.isna(row[column]) or row[column] == '':
                A.at[index, column] = b_dict[row['IFSC']].get(column, row[column])

# Add entries from B that are not in A
a_ifsc_set = set(A['IFSC'])
new_entries = B[~B['IFSC'].isin(a_ifsc_set)]

# Track progress for adding new entries
new_entries_list = []
for index, row in tqdm(new_entries.iterrows(), total=new_entries.shape[0], desc="Adding new entries from B", unit=" rows"):
    new_entries_list.append(row)

# Concatenate new entries to A
if new_entries_list:
    new_entries_df = pd.DataFrame(new_entries_list, columns=A.columns)
    A = pd.concat([A, new_entries_df], ignore_index=True)

# Save the merged dataframe to a new CSV file
A.to_csv('merged.csv', index=False)

print(f"Total entries in merged.csv: {len(A)}")
