"""
This module contains everything related to network topology processing
"""
import collections as coll
import heapq

Link = coll.namedtuple("Link", "dpid port_no")

class Network(object):
    """
    Container for all network state
    """

    def __init__():
        self.topo=TopologyDB()
        self.ip_to_mac={}
        self.mac_to_port= {} #for every MAC address=>{dpid,port_no}
        #Used to Update ports as given when a port event status changes

    def mac_of_ip(self, ip):
        """
        Returns mac of a given ip

        :param ip: 32b IP for a lookup
        :type ip: int

        :returns: 48b MAC
        :rtype: int
        """
        return self.ip_to_mac[ip]
        
    def port_of_mac(self,mac):
        """
        Returns dpid, port of a given Mac
        :param self: Self
        :type self: class object
        
        :param mac: mac address who's port no we wish to find
        :type mac: string
        
        :returns: integer port number
        :rtype: int
        """
        return self.mac_to_port[mac]
        
    def parse_ports(ports):
        self.topo[(dpid,port_no)]=(self._topo.P_LEARNING,None)
        pass

    def new_peer():
        pass

    def get_path(src_dpid,dst_dpid):
    #Gets the list of all the paths between core links
        pass


class TopologyDB(dict):

    P_EDGE=1
    P_CORE=2
    P_LEARNING=0
    """
    Topology graph with network related helpers
    """
    def spf():
        '''
        Returns nothing
        It stores a table of self_paths-> {(src,dst)=>[(dpid,port_no),(),()]}
        '''

    def _get_all_core(self):
        """
        Returns all links in P_CORE state

        :returns: list of links
        :rtype: list of (dpid, port_no)
        """
        return [k for k,v in self.items() if v[0] == self.P_CORE]
