import dace

sdfg = dace.SDFG("test_interstate_1")

state1 = sdfg.add_state("state1")
state2 = sdfg.add_state("state2")

sdfg.add_edge(state1, state2, dace.InterstateEdge(
    assignments={"a": 0}
))

sdfg.add_array("A", [1], dace.float32)

an = state2.add_access("A")
t = state2.add_tasklet("t", {}, {"out"}, "out = a")
state2.add_edge(t, "out", an, None, dace.Memlet("A[0]"))

sdfg.validate()

sdfg.save("test_interstate_1.sdfgz")

print("Arrays:", sdfg.arrays)
print("Symbols:", sdfg.symbols)
print("Constants:", sdfg.constants)
print("Free symbols:", sdfg.free_symbols)

sdfg.compile()