import dace
import os
from dace import nodes, dtypes, memlet
import copy

import sys
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory to the Python path
sys.path.append(current_dir)

from dace.sdfg.sdfg import InterstateEdge
from modules.map_over_tasklet import MapOverFreeTasklet

def fix_outgoing_incoming_edges_from_gpu_access_nodes(sdfg):
    for state in sdfg.states():
        for n in state.nodes():
            if isinstance(n, dace.nodes.AccessNode):
                # If data name is "gpu_*" but edge has "*" then replace it with "gpu_*"
                if n.data.startswith("gpu_"):
                    for oe in state.out_edges(n) + state.in_edges(n):
                        mem: dace.memlet.Memlet = oe.data
                        data_tokens = mem.data.split(".")
                        ndtk = []
                        for tok in data_tokens:
                            if tok == n.data[4:]:
                                ndtk.append(n.data)
                            else:
                                ndtk.append(tok)
                        new_data = ".".join(ndtk)
                        mem.data = new_data
            if isinstance(n, dace.nodes.NestedSDFG):
                fix_outgoing_incoming_edges_from_gpu_access_nodes(n.sdfg)

def force_copy_2(sdfg, force_copy_elements):
    for block in list(sdfg.all_control_flow_blocks()):
        for n in block.nodes():
            if isinstance(n, nodes.MapExit):
                for oe in block.out_edges(n):
                    if isinstance(oe.dst, nodes.AccessNode) and sdfg.arrays[oe.dst.data].storage == dtypes.StorageType.GPU_Global:
                        if oe.dst.data not in force_copy_elements:
                            continue
                        else:
                            # the gpu array with name N,
                            # add host array with name host_N

                            host_name = 'host_' + oe.dst.data
                            print(f"Apply Force-Copy: {oe.dst.data} -> {host_name}")
                            assert oe.dst.data in sdfg.arrays

                            if 'host_' + oe.dst.data not in sdfg.arrays:
                                host_desc = sdfg.arrays[oe.dst.data].clone()
                                host_desc.storage = dtypes.StorageType.Default
                                sdfg.arrays[host_name] = host_desc

                            # Re-route MapExit -> GPU AccessNode -> *
                            # Will become MapExit -> GPU AccessNode -> Host AccessNode -> *
                            assert type(oe.dst.data) == str

                            host_an = block.add_access(host_name)
                            block.add_edge(oe.dst, None, host_an, None, copy.deepcopy(oe.data))

                            # Change all interstate occurences to the host variant
                            for e in sdfg.edges():
                                e.data.replace(oe.dst.data, host_name)


def copy_out(sdfg, state_name:str, data:str):
    for state in sdfg.states():
        if state.label != state_name:
            continue

        moved = False
        for n in state.nodes():
            if (
                isinstance(n, dace.nodes.AccessNode) and
                n.data == data and
                len(state.out_edges(n)) == 0
            ):
                host_name = "host_" + data if not data.startswith("gpu_") else data[4:]

                if host_name not in sdfg.arrays:
                    host_desc = sdfg.arrays[n.data].clone()
                    host_desc.storage = dtypes.StorageType.Default
                    sdfg.arrays[host_name] = host_desc

                assert len(state.in_edges(n)) == 1
                m = state.in_edges(n)[0].data

                host_an = state.add_access(host_name)
                state.add_edge(n, None, host_an, None, copy.deepcopy(m))

                for e in sdfg.edges():
                    e.data.replace(data, host_name)
                moved = True
                break

        if not moved:
            host_name = "host_" + data if not data.startswith("gpu_") else data[4:]
            if host_name not in sdfg.arrays:
                host_desc = sdfg.arrays[n.data].clone()
                host_desc.storage = dtypes.StorageType.Default
                sdfg.arrays[host_name] = host_desc
            gpu_an = state.add_access(data)
            host_an = state.add_access(host_name)
            state.add_edge(gpu_an, None, host_an, None, dace.memlet.Memlet(f"{data}"))
            for e in sdfg.edges():
                e.data.replace(data, host_name)


def repl_intr_edges(sdfg, old_name, new_name):
    for e in sdfg.edges():
        e.data.replace(old_name, new_name)
    for s in sdfg.states():
        for n in s.nodes():
            if isinstance(n, dace.nodes.NestedSDFG):
                repl_intr_edges(n.sdfg, old_name, new_name)

velo_base_name = "velocity_tendencies_simplified_f.sdfgz"
velo2 = "sdfgs/velocity_tendencies_simplified_gpu_moft.sdfgz"
velo3 = "sdfgs/velocity_tendencies_simplified_gpu.sdfgz"
velo5 = "sdfgs/velocity_tendencies_simplified_gpu_forcecopy.sdfgz"
velo6 = "sdfgs/velocity_tendencies_simplified_gpu_forcecopy_simplified.sdfgz"
velo7 = "sdfgs/velocity_tendencies_simplified_gpu_forcecopy_simplified_loop_to_map.sdfgz"

skip_some_steps = True

if not skip_some_steps:
    velo_tendencies = dace.SDFG.from_file(velo_base_name)
    velo_tendencies.validate()


    velo_tendencies.apply_gpu_transformations(validate=False, validate_all=False, simplify=False)
    velo_tendencies.save(velo3)
    #velo_tendencies.validate()

    mapOverFreeTasklet = MapOverFreeTasklet()
    mapOverFreeTasklet.apply_pass(velo_tendencies, {"schedule_type": dace.dtypes.ScheduleType.GPU_Device})
    velo_tendencies.save(velo2)
    #velo_tendencies.validate()


    # Force copy-back on the kernel outputs (prune this to only the ones that are needed in interstate edges)
    force_copy_elements = ["z_w_con_c", "z_w_con_c_full", "vcflmax", "nflatlev", "levmask", "cfl_clipping", "levelmask"]


    repl_intr_edges(velo_tendencies, "v_p_metrics_ddqz_z_half", "p_metrics.ddqz_z_half")
    force_copy_2(velo_tendencies, force_copy_elements)

    velo_tendencies.save(velo5)
    velo_tendencies.validate()
    velo_tendencies.simplify(validate=False, validate_all=False)

    # Hand-made fixes
    def rm_assignment_to_view(sdfg, state_name, view_name):
        for state in sdfg.states():
            if state.label != state_name:
                continue

            d1 = False
            for n in state.nodes():
                if isinstance(n, dace.nodes.AccessNode) and n.data == view_name:
                    # Sanity checks: single incoming edge, no outgoing edge, and the assignment covers the whole view
                    # Then we can correctly rm the view
                    assert len(state.in_edges(n)) == 1
                    ie = state.in_edges(n)[0]
                    view : dace.data.Data = sdfg.arrays[n.data]
                    mem : dace.memlet.Memlet = ie.data
                    full_access_mem = dace.memlet.Memlet(data=f"{n.data}",
                                                        subset=dace.subsets.Range([(0,l-1,1) for l in view.shape]))

                    assert mem.subset.ranges == full_access_mem.subset.ranges
                    assert len(state.out_edges(n)) == 0
                    state.remove_node(n)

                    # If isolated nodes, rm them
                    for nn in state.nodes():
                        if len(state.in_edges(nn)) == 0 and len(state.out_edges(nn)) == 0:
                            state.remove_node(nn)
                    d1 = True
                if isinstance(n, dace.nodes.NestedSDFG):
                    d2 = rm_assignment_to_view(n.sdfg, state_name, view_name)
                    if d2:
                        d1 = d2
            return d1
        return False

    for state_name, view_name, struct_a_name in [("state_120_icopyout", "v_p_metrics_ddqz_z_half", "p_metrics.ddqz_z_half"),
                                                ("state_5_icopyout", "v_p_int_c_lin_e", "p_int.c_lin_e"),
                                                ("p_metrics_lifting", "v_p_metrics_ddqz_z_full_e", "p_metrics.ddqz_z_full_e")]:
        rmed = rm_assignment_to_view(velo_tendencies, state_name, view_name)
        assert rmed
        repl_intr_edges(velo_tendencies, view_name, struct_a_name)


    fix_outgoing_incoming_edges_from_gpu_access_nodes(velo_tendencies)

    velo_tendencies.save(velo6)
    velo_tendencies.validate()
else:
    velo_tendencies = dace.SDFG.from_file(velo6)

from dace.transformation.interstate import LoopToMap
velo_tendencies.apply_transformations_repeated(LoopToMap, validate_all=False, validate=False)
fix_outgoing_incoming_edges_from_gpu_access_nodes(velo_tendencies)
velo_tendencies.save(velo7)

velo_tendencies.validate()