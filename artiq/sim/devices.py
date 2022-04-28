from random import Random

from artiq.language.core import kernel, sequential, at_mu, delay_mu
from artiq.sim import time


class Core:
    def __init__(self, dmgr):
        self.ref_period = 1e-6
        self._level = 0

    def run(self, k_function, k_args, k_kwargs):
        self._level += 1
        with sequential:
            r = getattr(k_function.__self__, k_function.__name__).__wrapped__(k_function.__self__, *k_args, **k_kwargs)
        self._level -= 1
        if self._level == 0:
            print(time.manager.format_timeline())
            time.manager.timeline.clear()
        return r

    def seconds_to_mu(self, seconds):
        return round(seconds/self.ref_period)

    def mu_to_seconds(self, mu):
        return mu*self.ref_period

    def delay(self, seconds):
        delay_mu(self.seconds_to_mu(seconds))


class Input:
    def __init__(self, dmgr, name):
        self.core = dmgr.get("core")
        self.name = name
        self.prng = Random()

    @kernel
    def gate_rising(self, duration):
        time.manager.event(("gate_rising", self.name, duration))
        self.core.delay(duration)

    @kernel
    def gate_falling(self, duration):
        time.manager.event(("gate_falling", self.name, duration))
        self.core.delay(duration)

    @kernel
    def gate_both(self, duration):
        time.manager.event(("gate_both", self.name, duration))
        self.core.delay(duration)

    @kernel
    def count(self, up_to_timestamp_mu):
        result = self.prng.randrange(0, 100)
        time.manager.event(("count", self.name, result))
        return result

    @kernel
    def timestamp_mu(self, up_to_timestamp_mu):
        result = time.manager.get_time_mu()
        result += self.prng.randrange(100, 1000)
        time.manager.event(("timestamp_mu", self.name, result))
        at_mu(result)
        return result


class Output:
    def __init__(self, dmgr, name):
        self.core = dmgr.get("core")
        self.name = name

    @kernel
    def set_o(self, value):
        time.manager.event(("set", self.name, value))

    @kernel
    def pulse(self, duration):
        time.manager.event(("pulse", self.name, duration))
        self.core.delay(duration)

    @kernel
    def on(self):
        self.set_o(True)

    @kernel
    def off(self):
        self.set_o(False)


class WaveOutput:
    def __init__(self, dmgr, name):
        self.core = dmgr.get("core")
        self.name = name

    @kernel
    def pulse(self, frequency, duration):
        time.manager.event(("pulse", self.name, frequency, self.core.seconds_to_mu(duration)))
        self.core.delay(duration)


class VoltageOutput:
    def __init__(self, dmgr, name):
        self.core = dmgr.get("core")
        self.name = name

    @kernel
    def set(self, value):
        time.manager.event(("set_voltage", self.name, value))
