


"""
force_copy_elements = ["z_w_con_c", "z_w_con_c_full", "vcflmax", "nflatlev", "levmask", "cfl_clipping", "levelmask"]

def force_copy(sdfg, force_copy_elements):
    def replace_access_name(old_name, new_name, sdfg):
        for state in sdfg.states():
            for node in state.nodes():
                if isinstance(node, dace.nodes.AccessNode):
                    if node.data == old_name:
                        node.data = new_name
            for edge in state.edges():
                if edge.data is not None and edge.data.data is not None:
                    edge.data.data.replace(old_name, new_name)

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
                            print(f"Apply Force-Copy: {oe.dst.data} -> {gpu_name}")
                            assert 'host_' + oe.dst.data not in sdfg.arrays
                            gpu_desc = None
                            assert oe.dst.data in sdfg.arrays
                            gpu_desc = sdfg.arrays[oe.dst.data]
                            host_desc = sdfg.arrays[oe.dst.data].clone()
                            host_desc.storage = dtypes.StorageType.CPU_Heap
                            sdfg.arrays[gpu_name] = sdfg.arrays[oe.dst.data]
                            host_name = oe.dst.data
                            sdfg.arrays[host_name] = host_desc
                            #replace_access_name(host_name, gpu_name, sdfg)

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
"""

# Issue:
# "v_p_metrics_ddqz_z_half" has GPU storage, but accessed at interstate edge
# Need to discern between gpu_v_p* and v_p* and copy from GPU back

"""
should_not_be_gpu = ["v_p_metrics_ddqz_z_half"]

def discern_gpu_names(sdfg, names):
    # names is the list of names where they are stored in GPU but should not
    # Create gpu name by prepending gpu_
    # Replace all access nodes accordingly
    # Change descriptors
    # Find pattern (read from host, and change that one again)
    rpldict = {}
    for name in names:
        assert name in sdfg.arrays
        gpu_name = f"gpu_{name}"
        assert gpu_name not in sdfg.arrays
        assert sdfg.arrays[name].storage == dtypes.StorageType.GPU_Global
        rpldict[name] = gpu_name

    for block in list(sdfg.all_control_flow_blocks()):
        for n in block.nodes():
            if (isinstance(n, dace.nodes.AccessNode) and
                n.data in rpldict and
                sdfg.arrays[n.data].storage == dtypes.StorageType.GPU_Global):
                prev_name = n.data
                n.data = rpldict[n.data]
                # Change all memlet occurences
                for block in list(sdfg.all_control_flow_blocks()):
                    for e in block.edges():
                        m : dace.Memlet = e.data
                        if m.data is not None:
                            if prev_name in m.data:
                                print("Repl memlet data:", m.data, ",", prev_name, "-> ", n.data)
                                m.data.replace(prev_name, n.data)


    for name, gpu_name in rpldict.items():
        host_desc = sdfg.arrays[name].clone()
        host_desc.storage = dtypes.StorageType.Default
        gpu_desc = sdfg.arrays.pop(name, None)
        sdfg.arrays[gpu_name] = gpu_desc
        sdfg.arrays[name] = host_desc

    for block in list(sdfg.all_control_flow_blocks()):
        for n in block.nodes():
            if (isinstance(n, dace.nodes.AccessNode) and
                len(block.in_edges(n)) == 1 and
                isinstance(block.in_edges(n)[0].src, dace.nodes.AccessNode) and
                sdfg.arrays[block.in_edges(n)[0].src.data].storage != dtypes.StorageType.GPU_Global and
                sdfg.arrays[n.data].storage == dtypes.StorageType.GPU_Global):
                n.data = name
"""

