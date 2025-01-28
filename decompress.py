import dace

# Define the input and output file paths
input_file = 'velocity_tendencies_simplified_f_lex_apr.sdfgz'
output_file = 'velocity_tendencies_simplified_f_lex_apr.sdfg'

# Load the SDFG from the .sdfgz file
sdfg = dace.SDFG.from_file(input_file)

# Save the SDFG to the .sdfg file
sdfg.save(output_file)

print(f"File saved as {output_file}")