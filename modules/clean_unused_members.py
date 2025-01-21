import dace
import ast

class VariableCollector(ast.NodeVisitor):
    def __init__(self):
        self.variables = set()

    def visit_Name(self, node):
        self.variables.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Collect the full attribute name
        full_name = self._get_full_name(node)
        self.variables.add(full_name)
        self.generic_visit(node)

    def _get_full_name(self, node):
        if isinstance(node, ast.Attribute):
            return self._get_full_name(node.value) + '.' + node.attr
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return self._get_full_name(node.value)
        else:
            return ''

def get_variables_from_expr(expr):
    tree = ast.parse(expr)
    collector = VariableCollector()
    collector.visit(tree)
    return collector.variables

def clean_unused_members(sdfg: dace.SDFG, save_names: bool = False, save_as: str = None):
    # Find all data descriptors
    all_names = set()

    data_descriptors = sdfg.arrays.items()

    # Add both full name with dots and names of all members one by one
    def add_members(name, desc, depth, path):
        full_name = '.'.join(path + [name])
        if "." in name:
            raise Exception("uwu")
        all_names.add(name)
        #all_names.add(full_name)
        #print("\t" * depth, full_name, type(desc))
        if isinstance(desc, dace.data.Structure):
            for member_name, member in desc.members.items():
                add_members(member_name, member, depth + 1, path + [name])
        elif isinstance(desc, dace.data.ContainerArray):
            add_members(name, desc.stype, depth + 1, path + [name])

    for data_desc_name, data_desc in data_descriptors:
        add_members(data_desc_name, data_desc, 0, [])

    # Add symbols, all data descriptors and constants
    for sym in sdfg.symbols.keys():
        if "." in sym:
            raise Exception("owo1")
    for cons in sdfg.constants.keys():
        if "." in cons:
            raise Exception("owo2")
    for arr_name in sdfg.arrays.keys():
        if "." in arr_name:
            ts = arr_name.split(".")
            all_names = all_names.union(ts)
    all_names = all_names.union(sdfg.symbols.keys())
    all_names = all_names.union(sdfg.constants.keys())


    used_names = set()

    # All all accessed data from access nodes and memlets
    for cfg in sdfg.nodes():
        for node in cfg.nodes():
            if isinstance(node, dace.nodes.AccessNode):
                if "." in node.data:
                    used_names = used_names.union(node.data.split("."))
                else:
                    used_names.add(node.data)
            if isinstance(node, dace.nodes.Tasklet):
                # Should be handled by incoming memlets
                pass
        for edge in cfg.edges():
            if edge.data is not None:
                if edge.data.data is not None:
                    if "." in edge.data.data:
                        used_names = used_names.union(edge.data.data.split("."))
                    else:
                        used_names.add(edge.data.data)
    # Parse these things too...

    # Go through the interstate edges
    for edge in sdfg.edges():
        inter_edge : dace.InterstateEdge = edge.data
        accesses = set()
        for code in inter_edge.condition.code:
            vars = set()
            if isinstance(code, str) or isinstance(code, ast.Expr):
                vars = get_variables_from_expr(code)
            else:
                for c in code:
                    vars = vars.union(get_variables_from_expr(c))
            for var in vars:
                if "." in var:
                    accesses = accesses.union(var.split("."))
                else:
                    accesses.add(var)
        for a, a_str in inter_edge.assignments.items():
            vars = get_variables_from_expr(ast.parse(a_str))
            for var in vars:
                if "." in var:
                    accesses = accesses.union(var.split("."))
                else:
                    accesses.add(var)
            if "." in a:
                accesses = accesses.union(a.split("."))
            else:
                accesses.add(a)
        used_names = used_names.union(accesses)


    unused_names = set()
    for name in all_names:
        tokens = name.split(".")
        if "." in name:
            raise Exception("uwu")
        for t in tokens:
            if t not in used_names:
                unused_names.add(name)
                break

    unregistered_names =  used_names - all_names

    print("Unregistered names", unregistered_names)

    print("#All names:", len(all_names))
    print("#Unused names:", len(unused_names))
    print("#Used names:", len(used_names))
    print("#(Unused names + Used Names):", len(set.union(used_names, unused_names)))
    print("#Unregistered names:", len(unregistered_names))

    num_removed_arr = 0
    num_removed_member = 0
    num_removed_symbol = 0
    num_removed_constant = 0
    def try_del(name, src, arrays, d):
        nonlocal num_removed_arr, num_removed_member
        if name in arrays:
            if d == 0:
                assert src == sdfg
                sdfg.remove_data(name, validate=True)
                num_removed_arr += 1
            else:
                if "verts" == name:
                    pass
                    #print("1", src.members)
                    #print("2", src.free_symbols)
                    #print("3", arrays[name])
                del arrays[name]
                assert src._validate()
                num_removed_member += 1

        for arr_name, arr in arrays.items():
            if isinstance(arr, dace.data.Structure):
                assert arr._validate()
                try_del(name, arr, arr.members, d+1)

    for unused_name in unused_names:
        try_del(unused_name, sdfg, sdfg.arrays, 0)
        # TODO: try uncomment?
        #if unused_name in sdfg.symbols:
        #    sdfg.remove_symbol(unused_name)
        #    num_removed_symbol += 1
        #if unused_name in sdfg.constants:
        #    sdfg.remove_constant(unused_name)
        #    num_removed_constant += 1

    sdfg.validate()
    sdfg.compile()

    if save_as is not None:
        sdfg.save("sdfgs/velocity_tendencies_simplified_f_pruned.sdfgz")
    print("Removed", num_removed_arr, "arrays")
    print("Removed", num_removed_member, "members")
    print("Removed", num_removed_symbol, "symbols")
    print("Removed", num_removed_constant, "constants")

    if save_names:
        with open("unused_names.txt", "w") as f:
            for name in sorted(unused_names):
                f.write(name + "\n")
        with open("all_names.txt", "w") as f:
            for name in sorted(all_names):
                f.write(name + "\n")
        with open("used_names.txt", "w") as f:
            for name in sorted(used_names):
                f.write(name + "\n")
        with open("unregistered_names.txt", "w") as f:
            for name in sorted(unregistered_names):
                f.write(name + "\n")