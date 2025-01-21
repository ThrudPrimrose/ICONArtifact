import dace

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
        full_name = self._get_base_name(node)
        self.variables.add(full_name)
        self.generic_visit(node)

    def _get_base_name(self, node):
        if isinstance(node, ast.Attribute):
            return self._get_base_name(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return self._get_base_name(node.value)
        else:
            return ''

def get_variables_from_expr(expr):
    tree = ast.parse(expr)
    collector = VariableCollector()
    collector.visit(tree)
    return collector.variables

def clean_unused_members(sdfg: dace.SDFG):
    # Find all data descriptors
    all_members = set()

    data_descriptors = sdfg.arrays.items()

    # Print everything
    for data_desc_name, data_desc in data_descriptors:
        if isinstance(data_desc, dace.data.Structure):
            stack = [(data_desc_name, data_desc, 1)]
            while stack:
                current_name, current_desc, depth = stack.pop()
                print("\t" * depth, current_name, type(current_desc))
                if isinstance(current_desc, dace.data.Structure):
                    for member_name, member in current_desc.members.items():
                        stack.append((member_name, member, depth + 1))
                if isinstance(current_desc, dace.data.ContainerArray):
                    stack.append((current_name + "_ca", current_desc.stype, depth + 1))
        else:
            print(data_desc_name, type(data_desc))

    all_members = set()

    # Add both full name with dots and names of all members one by one
    def add_members(name, desc, depth, path):
        full_name = '.'.join(path + [name])
        if "." in name:
            raise Exception("uwu")
        all_members.add(name)
        #all_members.add(full_name)
        print("\t" * depth, full_name, type(desc))
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
            all_members = all_members.union(ts)
    all_members = all_members.union(sdfg.symbols.keys())
    all_members = all_members.union(sdfg.constants.keys())

    print(all_members)

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
            accesses = accesses.union(vars)
        for a, a_str in inter_edge.assignments.items():
            vars = get_variables_from_expr(ast.parse(a_str))
            accesses = accesses.union(vars)
            if "." in a:
                accesses = accesses.union(a.split("."))
            else:
                accesses.add(a)
        used_names = used_names.union(accesses)

    print("Used names", used_names)
    print("All names", all_members)

    unused_names = set()
    for name in all_members:
        tokens = name.split(".")
        if "." in name:
            raise Exception("uwu")
        for t in tokens:
            if t not in used_names:
                unused_names.add(name)
                break

    print("Unused names", unused_names)

    unregistered_names =  used_names - all_members
    print("Unregistered names", unregistered_names)
    print("#All names:", len(all_members))
    print("#Unused names:", len(unused_names))
    print("#Used names:", len(used_names))
    print("#(Unused names + Used Names):", len(set.union(used_names, unused_names)))
    print("#Unregistered names:", len(unregistered_names))

    num_removed_arr = 0
    num_removed_member = 0
    num_removed_symbol = 0
    num_removed_constant = 0
    def try_del(name, arrays, d):
        nonlocal num_removed_arr, num_removed_member
        if name in arrays:
            sdfg.remove_data(name)
            if d == 0:
                num_removed_arr += 1
            else:
                num_removed_member += 1

        for arr_name, arr in arrays.items():
            if isinstance(arr, dace.data.Structure):
                try_del(name, arr.members, d+1)

    for unused_name in unused_names:
        try_del(unused_name, sdfg.arrays, 0)
        #if unused_name in sdfg.symbols:
        #    sdfg.remove_symbol(unused_name)
        #    num_removed_symbol += 1
        #if unused_name in sdfg.constants:
        #    sdfg.remove_constant(unused_name)
        #    num_removed_constant += 1

    sdfg.save("sdfgs/velocity_tendencies_simplified_f_pruned.sdfgz")

    sdfg.validate()
    sdfg.save("sdfgs/velocity_tendencies_simplified_f_pruned.sdfgz")
    print("Removed", num_removed_arr, "arrays")
    print("Removed", num_removed_member, "members")
    print("Removed", num_removed_symbol, "symbols")
    print("Removed", num_removed_constant, "constants")
    sdfg.compile()