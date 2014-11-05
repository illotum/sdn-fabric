
class Topology (object):
    def __init_(self):
        self.links = set()  # [(dp, port, dp, port),..]
        self.paths = {}  # (dps, dpd): [(dp, port),..]

    def send_lldp(self, dp, port):
        pass
