"""
This module contains everything related to network topology processing
"""
from collections import defaultdict
import heapq


class Network(object):

    """
    Container for all network state
    """

    def __init__(self):
        self.topo = TopologyGraph()  # (src_dpid, dst_dpid) => port_no
        self.ip_to_mac = defaultdict()  # IP => MAC
        self.mac_to_port = defaultdict()  # MAC => (dpid,port_no)

    def mac_of_ip(self, ip):
        """
        Returns mac of a given IP

        :param ip: IP for a lookup
        :type ip: str

        :returns: associated MAC address or None
        :rtype: str
        """
        return self.ip_to_mac[ip]

    def port_of_mac(self, mac):
        """
        Returns dpid, port of a given MAC

        :param mac: MAC for a lookup
        :type mac: str

        :returns: dpid and port number or None
        :rtype: (int, int)
        """
        return self.mac_to_port[mac]

    def new_peer(self, dpid, peer, port_no):
        """
        Store new peering information

        :param dpid: datapath id of the reporting switch
        :type dpid: int

        :param peer: datapath id of the peer
        :type peer: int

        :param port_no: recieving port number
        :type port_no: int
        """
        self.topo[dpid, peer] = port_no
        self.topo.run_spf()

    def purge(self, dpid, port_no=None):
        """
        Cleanse all state from the given dpid or (dpid, port_no)

        :param dpid: datapath id to remove from all tables
        :type dpid: int

        :param port_no: port number to narrow down the cleanse;
                        all ports will be removed if not given
        :type port_no: int
        """
        print("PURGE OF " + str(dpid))


class TopologyGraph(defaultdict):
    """
    Topology graph with network related helpers.

    Stores unidirectional (peerA, PeerB) => out_port mappings.
    """

    def __init__(self, *args, **kwargs):
        self.switches = set()
        super(TopologyGraph, self).__init__(*args, **kwargs)

    @property
    def edges(self):
        """
        Return a list of internal edges of the current network topology.

        :returns: unidirectional internal links that are discovered so far
        :rtype: list of (peerA, peerB)
        """
        return self.keys()

    def run_spf(self):
        lst = [(a, b) for a in self.switches for b in self.switches if a != b]
        self.paths = defaultdict
        for src, dst in lst:
            self.paths[src, dst] = self.dijkstra(src, dst)

    def dijkstra(self, src, dst):
        """
        Compute the best path between two nodes.

        :param src: dpid of the starting switch
        :type src: int

        :param dst: dpid of the target switch
        :type dst: int

        :returns: best path to dst from src
        :rtype: list of int
        """
        graph = defaultdict(list)
        for a, b in self.edges:
            graph[a].append(b)

        queue = [(0, src, [])]
        seen = set()

        while queue:
            cost, a, path = heapq.heappop(queue)
            if a not in seen:
                seen.add(a)
                path = path + [a]  # FIXME: Not the most CPU effective way
                if a == dst:
                    return path  # Success
                for b in graph[a]:
                    if b not in seen:
                        heapq.heappush(queue, (cost+1, b, path))
        return None  # Failure

    def path_to_port(self, path, G, count=0):
        newPath = []
        while count < (len(path) - 1):
            src, dst = path[count], path[count + 1]
            newPath.append((src, G[src][dst]))
            count += 1
        return newPath
