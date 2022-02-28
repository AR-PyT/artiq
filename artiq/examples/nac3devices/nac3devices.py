from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.cache import CoreCache
from artiq.coredevice.zotino import Zotino
from artiq.coredevice.mirny import Mirny as MirnyCPLD
from artiq.coredevice.adf5356 import ADF5356
from artiq.coredevice.urukul import CPLD as UrukulCPLD
from artiq.coredevice.ad9912 import AD9912
from artiq.coredevice.sampler import Sampler
from artiq.coredevice.edge_counter import EdgeCounter
from artiq.coredevice.grabber import Grabber
from artiq.coredevice.fastino import Fastino


@nac3
class NAC3Devices(EnvExperiment):
    core: KernelInvariant[Core]
    core_cache: KernelInvariant[CoreCache]
    zotino0: KernelInvariant[Zotino]
    mirny0_cpld: KernelInvariant[MirnyCPLD]
    mirny0_ch0: KernelInvariant[ADF5356]
    urukul0_cpld: KernelInvariant[UrukulCPLD]
    urukul0_ch0: KernelInvariant[AD9912]
    sampler0: KernelInvariant[Sampler]
    ttl0_counter: KernelInvariant[EdgeCounter]
    grabber0: KernelInvariant[Grabber]
    fastino0: KernelInvariant[Fastino]

    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_cache")
        self.setattr_device("zotino0")
        self.setattr_device("mirny0_cpld")
        self.setattr_device("mirny0_ch0")
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul0_ch0")
        self.setattr_device("sampler0")
        self.setattr_device("ttl0_counter")
        self.setattr_device("grabber0")
        self.setattr_device("fastino0")

    @kernel
    def run(self):
        self.core.reset()
        self.zotino0.init()
        self.zotino0.set_leds(0x15)
        self.zotino0.set_dac([1.2, -5.3, 3.4, 4.5], [0, 1, 2, 3])

        self.core.break_realtime()
        self.mirny0_cpld.init()
        self.mirny0_ch0.init()
        self.mirny0_ch0.set_att_mu(160)
        self.mirny0_ch0.sw.on()
        self.mirny0_ch0.set_frequency(2500.*MHz)

        self.core.break_realtime()
        self.urukul0_cpld.init()
        self.urukul0_ch0.init()
        self.urukul0_ch0.sw.on()
        for i in range(10):
            self.urukul0_ch0.set((10. + float(i))*MHz)
            self.urukul0_ch0.set_att(6.)
            self.core.delay(500.*ms)

        self.core.break_realtime()
        self.sampler0.init()
        samples = [0. for _ in range(8)]
        self.sampler0.sample(samples)
