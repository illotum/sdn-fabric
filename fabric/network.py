"""
This module contains everything related to network topology processing
"""
import collections as coll
import heapq

Link = coll.namedtuple("Link", "dpid port_no")

class Network(object):
    """
    Container for all network state
    def __init__():
    self.topo=Topology()
    self.ip_to_mac={}
    self.mac_to_port={for every MAC address=>{dpid,port_no}
    #Used to Update ports as given when a port event status changes
    def parse_ports(ports):
    self._topo[(dpid,port_no)=(P_LEARNING,None)]
    pass
    """
    pass

class Topology(dict):
    """
    P_EDGE=1
    P_CORE=2
    P_LEARNING=0
    
    Topology graph with network related helpers
    """
class LinkState(object):
    '''
    LSDB STRUCTURE COULD BE:
    Dictionary[Dpid,P_no]=>Port State[None by default
    (dpid,port_no2):(type,data)]
    def __init__(self,dpid,port_no):
        self.paths={}
        # To check for uniqueness only between RID and port No but not port status
    def __eq__(self,other):
        return self.dpid==other.dpid and self.port_no==other.port_no
    def get_all_core():
    #Gets all core switches
    pass
    def get_path(src_dpid,dst_dpid):
    #Gets the list of all the paths between core links
    pass
    def spf():
    => Returns nothing.
    It stores a table of self_paths-> {(src,dst)=>[(dpid,port_no),(),()]
    '''
    pass
