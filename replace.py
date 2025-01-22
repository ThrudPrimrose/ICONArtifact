import gzip
import json

filename = "velocity_tendencies_simplified_f_lex_apr.sdfgz"
altered_filename = "sdfgs/velocity_tendencies_simplified_f_lex_apr_replaced.sdfgz"

repldict = {"ptr_patch": "p_patch"}

with gzip.open(filename, "rt", encoding="utf-8") as gz_file:
    content = gz_file.read()

for k, v in repldict.items():
    content = content.replace(k, v)

with gzip.open(altered_filename, "wt", encoding="utf-8") as gz_file:
    gz_file.write(content)