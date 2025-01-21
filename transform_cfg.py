import dace
import os
from dace import nodes, dtypes, memlet
import copy

velo_base_name = "velocity_tendencies_simplified_cfg.sdfgz"
velo2 = "sdfgs/velocity_tendencies_simplified_twice_cfg.sdfgz"

#if os.path.exists(velo3):
#    velo_tendencies = dace.SDFG.from_file(velo3)
#else:

print("LOAD BASE")
velo_tendencies = dace.SDFG.from_file(velo_base_name)
print("SIMPLIFY BASE")
velo_tendencies.simplify(validate_all=True)
print("VALIDATE")
velo_tendencies.validate()
velo_tendencies.save(velo2)
velo_tendencies.compile()