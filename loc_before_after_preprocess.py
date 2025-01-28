import os
import re

def preprocess_fortran(file_path, defined_flags, undefined_flags, ignored_flags):
    """
    Preprocesses a Fortran file by evaluating preprocessor directives
    with a given set of preprocessable flags while ignoring others.

    Args:
        file_path (str): Path to the Fortran file.
        preprocess_flags (set): Set of flags that should be preprocessed.
        ignored_flags (set): Set of flags that should not be preprocessed.

    Returns:
        tuple: Original lines of code, preprocessed lines of code.
    """
    original_lines = []
    processed_lines = []

    with open(file_path, 'r') as f:
        skip_block = False  # Whether to skip the current block of code
        for line in f:
            original_lines.append(line)

            # Skip pragma lines for OpenACC, OpenMP, etc.
            if re.match(r'^\s*![$](ACC|DIR|NEC|OMP|DIR)', line):
                continue  # Skip these lines

            # Handle preprocessor directives
            ifdef_match = re.match(r'^\s*#(ifdef|ifndef)\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            ifdef_defined_match = re.match(r'^\s*#if\s+defined\((\w+)\)', line)
            endif_match = re.match(r'^\s*#endif', line)
            else_match = re.match(r'^\s*#else', line)

            if ifdef_match:
                directive, macro = ifdef_match.groups()
                if directive == "ifdef":
                    skip_block = macro in undefined_flags and macro not in ignored_flags
                elif directive == "ifndef":
                    skip_block = macro in defined_flags and macro not in ignored_flags
            elif ifdef_defined_match:
                macro = ifdef_defined_match.group(1)
                skip_block = macro in defined_flags and macro not in ignored_flags
            elif endif_match:
                skip_block = False
            elif else_match:
                # Toggle the block inclusion when #else is encountered
                skip_block = not skip_block
            elif not skip_block:
                # Include the line if it's not in a skipped block
                processed_lines.append(line)

    return original_lines, processed_lines


def process_directory(directory, defined_falgs, undefined_flags, ignored_flags):
    """
    Processes all Fortran files in a directory, comparing lines of code before
    and after preprocessing.

    Args:
        directory (str): Path to the root directory.
        preprocess_flags (set): Set of flags that should be preprocessed.
        ignored_flags (set): Set of flags that should not be preprocessed.

    Returns:
        dict: A dictionary mapping file paths to (original LOC, preprocessed LOC).
    """
    results = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.f', '.f90', '.F', '.F90')):  # Fortran file extensions
                file_path = os.path.join(root, file)
                original_lines, processed_lines = preprocess_fortran(
                    file_path, defined_flags, undefined_flags, ignored_flags
                )
                if file == "mo_velocity_advection.f90":
                    with open("prp.f90", "w") as f:
                        f.write("".join(processed_lines))
                results[file_path] = (len(original_lines), len(processed_lines))
    return results


if __name__ == "__main__":
    # Specify the root directory containing Fortran code
    folder_path = "./icon-dace-integration/src/atm_dyn_iconam"  # Change this to your folder path

    # Define the macros to preprocess and to ignore
    ignored_flags =  {'MESSY', 'HAVE_RADARFWO', '__MIXED_PRECISION', '__ENABLE_DDT_VN_XYZ__',
                    'MESSYTIMER', '__ICON_ART', 'NOMPI', '__NO_ICON_COMIN__', '__NO_ICON_UPATMO__',
                      '__NO_ICON_LES__', '__NO_NWP__', '__SX__', '__SWAPDIM', 'YAC_coupling', '__NO_JSBACH__',
                      '__NO_AES__'}
    defined_flags = {"__LOOP_EXCHANGE"}
    undefined_flags = {"_OPENACC", "INTEL_COMPILER", "_OPENMP", "__PGI", "_CRAYFTN", "__INTEL_COMPILER"}

    # Process the directory and get line count comparisons
    results = process_directory(folder_path, defined_flags, undefined_flags, ignored_flags)

    # Print the results
    for file_path, (original_loc, preprocessed_loc) in results.items():
        print(f"File: {file_path}")
        print(f"  Original LOC: {original_loc}")
        print(f"  Preprocessed LOC: {preprocessed_loc}")
        print(f"  Difference: {original_loc - preprocessed_loc}")
        print()
