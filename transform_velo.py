import dace
import os
from dace import nodes, dtypes, memlet
import copy

velo_base_name = "velocity_tendencies_simplified_f.sdfgz"
velo2 = "sdfgs/velocity_tendencies_simplified_cfg.sdfgz"
velo3 = "sdfgs/velocity_tendencies_simplified_cfg_gpu.sdfgz"
velo4 = "sdfgs/velocity_tendencies_simplified_cfg_gpu_forcecopy.sdfgz"

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
print("APPLY GPU TRANSFORMATION")
velo_tendencies.apply_gpu_transformations(validate=False, validate_all=False, simplify=False)
velo_tendencies.save(velo3)

# Force copy-back on the kernel outputs (prune this to only the ones that are needed in interstate edges)

force_copy_elements = ["z_w_con_c", "z_w_con_c_full", "vcflmax", "nflatlev"]

def force_copy(sdfg, force_copy_elements):
    def replace_access_name(old_name, new_name, sdfg):
        for state in sdfg.states():
            for node in state.nodes():
                if isinstance(node, dace.nodes.AccessNode):
                    if node.data == old_name:
                        node.data = new_name
            for edge in state.edges():
                if edge.data.data == old_name:
                    edge.data.data = new_name

    for block in list(sdfg.all_control_flow_blocks()):
        for n in block.nodes():
            if isinstance(n, nodes.MapExit):
                for oe in block.out_edges(n):
                    if isinstance(oe.dst, nodes.AccessNode) and sdfg.arrays[oe.dst.data].storage == dtypes.StorageType.GPU_Global:
                        if oe.dst.data not in force_copy_elements:
                            continue
                        else:
                            # the gpu array with name N becomes gpu_N,
                            # N is now the host data
                            gpu_name = 'gpu_' + oe.dst.data
                            assert 'host_' + oe.dst.data not in sdfg.arrays
                            gpu_desc = None
                            assert oe.dst.data in sdfg.arrays
                            gpu_desc = sdfg.arrays[oe.dst.data]
                            host_desc = sdfg.arrays[oe.dst.data].clone()
                            host_desc.storage = dtypes.StorageType.CPU_Heap
                            sdfg.arrays[gpu_name] = sdfg.arrays[oe.dst.data]
                            host_name = oe.dst.data
                            sdfg.arrays[host_name] = host_desc
                            replace_access_name(host_name, gpu_name, sdfg)

                            # Re-route MapExit -> GPU AccessNode -> *
                            # Will become MapExit -> GPU AccessNode -> Host AccessNode -> *
                            an_out_edges = block.out_edges(oe.dst)
                            host_access = block.add_access(host_name)
                            assert type(oe.dst.data) == str

                            edges_to_rm = []
                            for an_out_edge in an_out_edges:
                                edges_to_rm.append(an_out_edge)
                                _, u_conn, v, v_conn, m = an_out_edge
                                mcopy : memlet.Memlet = copy.deepcopy(m)
                                mcopy.data = host_name
                                block.add_edge(host_access, u_conn, v, v_conn, mcopy)

                            block.add_edge(oe.dst, None, host_access, None, memlet.Memlet(expr=oe.dst.data))

                            for e in edges_to_rm:
                                block.remove_edge(e)

print("APPLY FORCE COPY")
force_copy(velo_tendencies, force_copy_elements)
print("VALIDATE GPU")
velo_tendencies.validate()

velo_tendencies.save(velo4)