import dace
from dace.transformation.passes.simplify import SimplifyPass


SDFG_FILE_PATHS = [
    #'validated.sdfgz',
    #'simplified.sdfgz',
    #'test_interstate_1.sdfgz',
    'velocity_tendencies_simplified_f_lex_apr.sdfgz',
    #'velocity_tendencies_simplified_f_phil.sdfgz',
    #'sdfgs/velocity_tendencies_simplified_f_lex_apr_replaced.sdfgz',
    #'sdfgs/velocity_tendencies_simplified_f_lex_apr_replaced_pruned.sdfgz',
]

from dace.transformation.pass_pipeline import FixedPointPipeline
from dace.transformation.passes.lift_struct_views import LiftStructViews

def process_sdfg():
    for p in SDFG_FILE_PATHS:
        print(f"Simplify-Validate-Compile: {p}")
        #try:
        sdfg = dace.SDFG.from_file(p)
        print("1")
        sdfg.validate()
        print("2")
        #sdfg.simplify(validate_all=False, validate=False, options={"skip": set(["LiftStructViews"])})
        SimplifyPass(validate_all=False, validate=False, skip=set(["LiftStructViews"])).apply_pass(sdfg, {})
        #FixedPointPipeline([LiftStructViews()]).apply_pass(sdfg, {})
        sdfg.save("sfull.sdfgz")
        print("3")
        sdfg.validate()
        print("4")
        sdfg.compile()
        #print(f"Simplify-Validate-Compile Succesful for {p}.")
        #except Exception as e:
        #print(f"Simplify-Validate-Compile Failed for {p}. Error: {e}")


if __name__ == "__main__":
    process_sdfg()