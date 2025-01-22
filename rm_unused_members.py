import sys
import dace
import os

velo_base_name = "sdfgs/velocity_tendencies_simplified_f_lex_apr_replaced.sdfgz"
velo_tendencies = dace.SDFG.from_file(velo_base_name)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from modules.clean_unused_members import clean_unused_members

clean_unused_members(velo_tendencies, True, "sdfgs/velocity_tendencies_simplified_f_lex_apr_replaced_pruned.sdfgz")
