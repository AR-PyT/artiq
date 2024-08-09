# RUN: %python -m artiq.compiler.testbench.jit %s >%t
# RUN: OutputCheck %s --file-to-check=%t
# REQUIRES: exceptions

@kernel
def raise_error(fn):
    try:
        fn()
    except Exception as e:
        print(e)

def raise_ZeroDivisionError():
    1/0

def raise_IndexError():
    [1.0][10]

def raise_ValueError():
    raise ValueError

def raise_RuntimeError():
    raise RuntimeError

def raise_AssertError():
    assert False, "foo"

def raise_KeyError():
    raise KeyError

def raise_NotImplementedError():
    raise NotImplementedError

def raise_OverflowError():
    raise OverflowError

def raise_IOError():
    raise IOError

raise_error(raise_ZeroDivisionError)
raise_error(raise_IndexError)
raise_error(raise_ValueError)
raise_error(raise_RuntimeError)
raise_error(raise_AssertError)
raise_error(raise_KeyError)
raise_error(raise_NotImplementedError)
raise_error(raise_OverflowError)
raise_error(raise_IOError)

# CHECK-L: 9(0, 0, 0)
# CHECK-L: 10(10, 1, 0)
# CHECK-L: 11(0, 0, 0)
# CHECK-L: 12(0, 0, 0)
# CHECK-L: 13(0, 0, 0)
# CHECK-L: 14(0, 0, 0)
# CHECK-L: 15(0, 0, 0)
# CHECK-L: 16(0, 0, 0)
# CHECK-L: 17(0, 0, 0)
