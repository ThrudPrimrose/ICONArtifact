import dace
import sys

branch = sys.argv[1]
velo_base_name = "velocity_tendencies_simplified_f.sdfgz"
print("LOAD NON CFG")

branch = sys.argv[1]
log_file = "sdfg_results.log"
with open(log_file, "a") as f:
    try:
        velo_tendencies = dace.SDFG.from_file(velo_base_name)
        f.write(f"{branch}: succesfully loaded SDFG\n")
    except Exception as e:
        f.write(f"{branch}: did not succesfully load SDFG\n")
        print("Error:", e)
    try:
        velo_tendencies.compile()
        f.write(f"{branch}: succesfully compiled SDFG\n")
    except Exception as e:
        f.write(f"{branch}: did not succesfully compile SDFG\n")
        print("Error:", e)

    velo_base_name_cfg = "velocity_tendencies_simplified_cfg.sdfgz"
    print("LOAD CFG")

    try:
        velo_tendencies_cfg = dace.SDFG.from_file(velo_base_name_cfg)
        f.write(f"{branch}: succesfully loaded CFG SDFG\n")
    except Exception as e:
        f.write(f"{branch}: did not succesfully load CFG SDFG\n")
        print("Error:", e)
    try:
        velo_tendencies_cfg.compile()
        f.write(f"{branch}: succesfully compiled CFG SDFG\n")
    except Exception as e:
        f.write(f"{branch}: did not succesfully compile CFG SDFG\n")
        print("Error:", e)

