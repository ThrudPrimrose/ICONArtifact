import shutil
import os

# Define the source files and destination directory
source_files = [
    'sdfgs/velocity_tendencies_simplified_f_lex_apr_replaced_pruned.sdfgz',
    'used_names.txt'
]
destination_dir = 'icon-dace-integration/sdfgs'

# Ensure the destination directory exists
os.makedirs(destination_dir, exist_ok=True)

# Copy each file to the destination directory
for file in source_files:
    shutil.copy(file, destination_dir)

print("Files copied successfully.")