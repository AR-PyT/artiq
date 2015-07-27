from migen.fhdl.std import *
from migen.bank.description import *
from migen.bank import wbgen
from mibuild.generic_platform import *
from mibuild.xilinx.vivado import XilinxVivadoToolchain
from mibuild.xilinx.ise import XilinxISEToolchain

from misoclib.com import gpio
from misoclib.soc import mem_decoder
from misoclib.mem.sdram.core.minicon import MiniconSettings
from targets.kc705 import MiniSoC

from artiq.gateware.soc import AMPSoC
from artiq.gateware import rtio, nist_qc1, nist_qc2
from artiq.gateware.rtio.phy import ttl_simple, dds


class _RTIOCRG(Module, AutoCSR):
    def __init__(self, platform, rtio_internal_clk):
        self._clock_sel = CSRStorage()
        self.clock_domains.cd_rtio = ClockDomain(reset_less=True)

        rtio_external_clk = Signal()
        user_sma_clock = platform.request("user_sma_clock")
        platform.add_period_constraint(user_sma_clock.p, 8.0)
        self.specials += Instance("IBUFDS",
                                  i_I=user_sma_clock.p, i_IB=user_sma_clock.n,
                                  o_O=rtio_external_clk)
        self.specials += Instance("BUFGMUX",
                                  i_I0=rtio_internal_clk,
                                  i_I1=rtio_external_clk,
                                  i_S=self._clock_sel.storage,
                                  o_O=self.cd_rtio.clk)


class _NIST_QCx(MiniSoC, AMPSoC):
    csr_map = {
        "rtio": None,  # mapped on Wishbone instead
        "rtio_crg": 13,
        "kernel_cpu": 14,
        "rtio_moninj": 15
    }
    csr_map.update(MiniSoC.csr_map)
    mem_map = {
        "rtio":     0x20000000, # (shadow @0xa0000000)
        "mailbox":  0x70000000  # (shadow @0xf0000000)
    }
    mem_map.update(MiniSoC.mem_map)

    def __init__(self, platform, cpu_type="or1k", **kwargs):
        MiniSoC.__init__(self, platform,
                         cpu_type=cpu_type,
                         sdram_controller_settings=MiniconSettings(l2_size=128*1024),
                         with_timer=False, **kwargs)
        AMPSoC.__init__(self)
        self.submodules.leds = gpio.GPIOOut(Cat(
            platform.request("user_led", 0),
            platform.request("user_led", 1)))

    def add_rtio(self, rtio_channels):
        self.submodules.rtio_crg = _RTIOCRG(self.platform, self.crg.pll_sys)
        self.submodules.rtio = rtio.RTIO(rtio_channels)
        self.add_constant("RTIO_FINE_TS_WIDTH", self.rtio.fine_ts_width)
        self.add_constant("DDS_RTIO_CLK_RATIO", 8 >> self.rtio.fine_ts_width)
        self.submodules.rtio_moninj = rtio.MonInj(rtio_channels)

        if isinstance(self.platform.toolchain, XilinxVivadoToolchain):
            self.platform.add_platform_command("""
create_clock -name rsys_clk -period 8.0 [get_nets {rsys_clk}]
create_clock -name rio_clk -period 8.0 [get_nets {rio_clk}]
set_false_path -from [get_clocks rsys_clk] -to [get_clocks rio_clk]
set_false_path -from [get_clocks rio_clk] -to [get_clocks rsys_clk]
""", rsys_clk=self.rtio.cd_rsys.clk, rio_clk=self.rtio.cd_rio.clk)
        if isinstance(self.platform.toolchain, XilinxISEToolchain):
            self.platform.add_platform_command("""
NET "sys_clk" TNM_NET = "GRPrsys_clk";
NET "{rio_clk}" TNM_NET = "GRPrio_clk";
TIMESPEC "TSfix_cdc1" = FROM "GRPrsys_clk" TO "GRPrio_clk" TIG;
TIMESPEC "TSfix_cdc2" = FROM "GRPrio_clk" TO "GRPrsys_clk" TIG;
""", rio_clk=self.rtio_crg.cd_rtio.clk)

        rtio_csrs = self.rtio.get_csrs()
        self.submodules.rtiowb = wbgen.Bank(rtio_csrs)
        self.kernel_cpu.add_wb_slave(mem_decoder(self.mem_map["rtio"]),
                                     self.rtiowb.bus)
        self.add_csr_region("rtio", self.mem_map["rtio"] | 0x80000000, 32,
                            rtio_csrs)


class NIST_QC1(_NIST_QCx):
    def __init__(self, platform, cpu_type="or1k", **kwargs):
        _NIST_QCx.__init__(self, platform, cpu_type, **kwargs)
        platform.add_extension(nist_qc1.fmc_adapter_io)

        self.comb += [
            platform.request("ttl_l_tx_en").eq(1),
            platform.request("ttl_h_tx_en").eq(1)
        ]

        rtio_channels = []
        for i in range(2):
            phy = ttl_simple.Inout(platform.request("pmt", i))
            self.submodules += phy
            rtio_channels.append(rtio.Channel.from_phy(phy, ififo_depth=512))
        for i in range(15):
            phy = ttl_simple.Output(platform.request("ttl", i))
            self.submodules += phy
            rtio_channels.append(rtio.Channel.from_phy(phy))

        phy = ttl_simple.Output(platform.request("user_led", 2))
        self.submodules += phy
        rtio_channels.append(rtio.Channel.from_phy(phy))
        self.add_constant("RTIO_REGULAR_TTL_COUNT", len(rtio_channels))

        phy = ttl_simple.ClockGen(platform.request("ttl", 15))
        self.submodules += phy
        rtio_channels.append(rtio.Channel.from_phy(phy))

        self.add_constant("RTIO_DDS_CHANNEL", len(rtio_channels))
        self.add_constant("DDS_CHANNEL_COUNT", 8)
        self.add_constant("DDS_AD9858")
        phy = dds.AD9858(platform.request("dds"), 8)
        self.submodules += phy
        rtio_channels.append(rtio.Channel.from_phy(phy,
                                                   ofifo_depth=512,
                                                   ififo_depth=4))
        self.add_rtio(rtio_channels)


class NIST_QC2(_NIST_QCx):
    def __init__(self, platform, cpu_type="or1k", **kwargs):
        _NIST_QCx.__init__(self, platform, cpu_type, **kwargs)
        platform.add_extension(nist_qc2.fmc_adapter_io)

        rtio_channels = []
        for i in range(16):
            if i == 14:
                # TTL14 is for the clock generator
                continue
            if i % 4 == 3:
                phy = ttl_simple.Inout(platform.request("ttl", i))
                self.submodules += phy
                rtio_channels.append(rtio.Channel.from_phy(phy, ififo_depth=512))
            else:
                phy = ttl_simple.Output(platform.request("ttl", i))
                self.submodules += phy
                rtio_channels.append(rtio.Channel.from_phy(phy))

        phy = ttl_simple.Output(platform.request("user_led", 2))
        self.submodules += phy
        rtio_channels.append(rtio.Channel.from_phy(phy))
        self.add_constant("RTIO_REGULAR_TTL_COUNT", len(rtio_channels))

        phy = ttl_simple.ClockGen(platform.request("ttl", 14))
        self.submodules += phy
        rtio_channels.append(rtio.Channel.from_phy(phy))

        self.add_constant("RTIO_DDS_CHANNEL", len(rtio_channels))
        self.add_constant("DDS_CHANNEL_COUNT", 11)
        self.add_constant("DDS_AD9914")
        self.add_constant("DDS_ONEHOT_SEL")
        phy = dds.AD9914(platform.request("dds"), 11)
        self.submodules += phy
        rtio_channels.append(rtio.Channel.from_phy(phy,
                                                   ofifo_depth=512,
                                                   ififo_depth=4))
        self.add_rtio(rtio_channels)


default_subtarget = NIST_QC1
