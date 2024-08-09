import unittest

from artiq.experiment import *
from artiq.test.hardware_testbench import ExperimentCase
from artiq.coredevice.exceptions import *
from artiq.coredevice.core import test_exception

"""
Test sync between exceptions raised between host and kernel

Need to have test cases where error is returned from kernel and the key matches here in host
No previous issue of syncing because of LLVM-IR generation beforehand
Needs to throw exceptions from runtime functions like LinAlg, that will indeed require the error handling to be implemented correctly
For most code that you will write need not to worry about the error but for some there is

For this file, provide test cases but since most have already been spread out throughout => bring them together into one block that can test the exception throwing completely
Remove redundant application from catch_all since that no longer needs to be considered
"""

[
    "RTIOUnderflow",
    "RTIOOverflow",
    "RTIODestinationUnreachable",
    "DMAError",
    "I2CError",
    "CacheError",
    "SPIError",
    "SubkernelError",

    "0:AssertionError",
    "0:AttributeError",
    "0:IndexError",
    "0:IOError",
    "0:KeyError",
    "0:NotImplementedError",
    "0:OverflowError",
    "0:RuntimeError",
    "0:TimeoutError",
    "0:TypeError",
    "0:ValueError",
    "0:ZeroDivisionError"
]


# AssertionError
# AttributeError
# CacheError
# DefaultMissing
# exceptions.DMAError
# I2CError
# IndexError
# KeyError
# KeyError, "device_db"
# KeyError, "dummy"
# _MyException
# OverflowError
# RPCReturnValueError
# RTIOOverflow
# RTIOUnderflow
# TimeoutError
# TypeError
# ValueError
# WorkerInternalException
# WorkerWatchdogTimeout
# ZeroDivisionError

class _TestExceptions(EnvExperiment):
    def build(self):
        self.setattr_device("core")
    
    @kernel
    def raise_exception(self, id):
        test_exception(id)

    
class ExceptionTest(ExperimentCase):
    def test_raise_exceptions(self):
        pass
    def test_exceptions(self):
        exp = self.create(_TestExceptions)
        with self.assertRaises(RTIOUnderflow) as ctx:
            exp.raise_exception(1)
        self.assertEqual(str(ctx.exception), "RTIOUnderflow")

        with self.assertRaises(RTIOOverflow) as ctx:
            exp.raise_exception(2)
        self.assertEqual(str(ctx.exception), "RTIOOverflow")

        with self.assertRaises(RTIODestinationUnreachable) as ctx:
            exp.raise_exception(3)
        self.assertEqual(str(ctx.exception), "RTIODestinationUnreachable")

        with self.assertRaises(DMAError) as ctx:
            exp.raise_exception(4)
        self.assertEqual(str(ctx.exception), "DMAError")
        
        with self.assertRaises(I2CError) as ctx:
            exp.raise_exception(5)
        self.assertEqual(str(ctx.exception), "I2CError")
            
        with self.assertRaises(CacheError) as ctx:
            exp.raise_exception(6)
        self.assertEqual(str(ctx.exception), "CacheError")

        with self.assertRaises(SPIError) as ctx:
            exp.raise_exception(7)
        self.assertEqual(str(ctx.exception), "SPIError")

        with self.assertRaises(SubkernelError) as ctx:
            exp.raise_exception(8)
        self.assertEqual(str(ctx.exception), "SubkernelError")

        with self.assertRaises(ZeroDivisionError) as ctx:
            exp.raise_exception(9)
        self.assertEqual(str(ctx.exception), "ZeroDivisionError")

        with self.assertRaises(RuntimeError) as ctx:
            exp.raise_exception(12)
        self.assertEqual(str(ctx.exception), "AssertionError")
        
