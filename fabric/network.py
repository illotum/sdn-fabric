"""
This module contains everything related to network topology processing
"""
from collections import defaultdict
import heapq
from fabric.pqdict import PQDict


class Network(object):

    """
    Container for all network state
    """

    def __init__():
        self.topo = TopologyDB()
        self.ip_to_mac = defaultdict(None)  # IP => MAC
        self.mac_to_port = defaultdict(None)  # MAC => (dpid,port_no)
        list_of_paths_between_core_links = []

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

        :returns: dpid and port number
        :rtype: (int, int)
        """
        return self.mac_to_port[mac]

    def parse_ports(ports):
        self.topo[(dpid, port_no)] = (self._topo.P_LEARNING, None)
        pass

    def new_peer():
        pass

    def get_path(src_dpid, dst_dpid):
        # Gets the list of all the paths between core links
        pass


class TopologyDB(dict):

    P_EDGE = 1
    P_CORE = 2
    P_LEARNING = 0
    """
    Topology graph with network related helpers
    """
    def spf(lsdb):
        '''
        It stores a table of self_paths-> {(src,dst)=>[(dpid,port_no),(),()]}

        returns a list of src,dst=> dpid,port_no
        '''
        neighbourTable = self.neighbour_discovery(lsdb)
        for i in neighbourTable.keys():
            for j in neighbourTable.keys():
                if i is not j:
                    self_paths[(i, j)] = self.shortestPath(
                        neighbourTable, i, j)
        return self_paths

    def get_all_core(self, lsdb, coreLinks=[]):
        """
        Returns all links in P_CORE state

        :returns: list of links
        :rtype: list of (dpid, port_no)
        """
        for x in lsdb.keys():
            if lsdb[x][0] is 2:
                coreLinks.append((x, lsdb[x][1]))
        return coreLinks

    def active_core_links(self, lsdb):
        """
        Returns all links which are Active and connected to another switch
        :returns: Dictionary of active_links
        :return Type: Dictionary
        """
        activeLinks = {}
        for x in lsdb.keys():
            if lsdb[x][0] is 2:
                activeLinks[x] = lsdb[x][1]
        return activeLinks

    def neighbour_discovery(self, lsdb, topoTable={}):
        """
        :param lsdb: link state data base
        :type lsdb: Dictionary

        :param topoTable: topology table.
        :type topoTable: Dictionary
        """
        dlink = self.active_core_links(lsdb)
        for x, y in dlink.keys():
            if x not in topoTable:
                topoTable[x] = {dlink[(x, y)]: y}
            else:
                topoTable[x][dlink[(x, y)]] = y
        return topoTable

    def shortestPath(self, G, start, end):
        D, P = self.Dijkstra(G, start, end)
        Path = []
        while 1:
            Path.append(end)
            if end == start:
                break
            end = P[end]
        Path.reverse()
        Path = self.path_to_port(Path, G)
        return Path

    def Dijkstra(self, G, start, end=None):
        """
        Computes Djikstras algorithm to get best paths
        """
        D = {}  # dictionary of final distances
        P = {}  # dictionary of predecessors
        Q = PQDict()   # est.dist. of non-final vert.
        Q[start] = 0

        for v in Q:
            D[v] = Q[v]
            if v == end:
                break

            for w in G[v]:
                vwLength = D[v] + 1
                if w in D:
                    if vwLength < D[w]:
                        raise ValueError, \
                            "Dijkstra: found better path to already-final vertex"
                elif (w not in Q) or (vwLength < Q[w]):
                    Q[w] = vwLength
                    P[w] = v

        return D, P

    def path_to_port(self, path, G, count=0):
        newPath = []
        while count < (len(path) - 1):
            src, dst = path[count], path[count + 1]
            newPath.append((src, G[src][dst]))
            count += 1
        return newPath
