import dace
import os
from dace import nodes, dtypes, memlet
import copy

velo1 = "velocity_tendencies_simplified_f.sdfgz"
velo2 = "sdfgs/velocity_tendencies_simplified_gpu.sdfgz"
velo3 = "sdfgs/velocity_tendencies_simplified_gpu_moft.sdfgz"
velo4 = "sdfgs/velocity_tendencies_simplified_gpu_forcecopy.sdfgz"
velo5 = "sdfgs/velocity_tendencies_simplified_gpu_forcecopy_simplified.sdfgz"
velo6 = "sdfgs/velocity_tendencies_simplified_gpu_forcecopy_simplified_loop_to_map.sdfgz"

for vname in [velo1, velo2, velo3, velo4, velo5, velo6]:
    try:
        print(f"Compile {vname}")
        velo_tendencies = dace.SDFG.from_file(vname)
        velo_tendencies.compile()
        print(f"Compiling {vname} successful.")
    except Exception as e:
        print(f"Compiling {vname} failed, reason: {e}")

velo_tendencies = dace.SDFG.from_file(velo6)
velo_tendencies.compile()