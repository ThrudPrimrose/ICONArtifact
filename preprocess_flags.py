import os
import re

def find_unique_definitions(directory):
    """
    Finds unique preprocessor definitions (e.g., `ifdef`, `ifndef`, `if defined(...)`)
    in Fortran files across a directory tree.
    
    Args:
        directory (str): Path to the root directory.

    Returns:
        set: A set of unique definitions.
    """
    definitions = set()
    # Regex patterns to match ifdef, ifndef, and if defined(...)
    pattern = re.compile(r'\b(ifdef|ifndef|if\s+defined)\s*\(?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)?')

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.f', '.f90', '.F', '.F90')):  # Fortran file extensions
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        match = pattern.search(line)
                        if match:
                            definitions.add(match.group(2))
    return definitions

if __name__ == "__main__":
    # Specify the root directory containing Fortran code
    folder_path = "./icon-dace-integration/src/atm_dyn_iconam"  # Change this to your folder path

    unique_definitions = find_unique_definitions(folder_path)
    print(f"Unique definitions: {unique_definitions}")
    print(f"Total unique definitions: {len(unique_definitions)}")
