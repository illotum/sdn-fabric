"""
This module containes pure functions to parse and craft packets.
"""

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import lldp

def create_lldp(dpid,port_no=DEFAULT_VALUE):
    '''
    Ryu.packet_lldp()
    '''
    pass

def create_arp( dl_src,dl_dst,nl_src,nl_dst):
    '''
    => ARP()
    '''
    pass

def parse_eth(data):
    pass

def parse_lldp(decr,data):
    '''
    => (descr dictionary is built and descr is returned)
    
    '''
    pass

def parse_arp(descr,data):
    '''
    Same as parse_lldp
    '''
    pass

def parse(data):
    '''
    {"dl_type:","dl_src":}
    eth.header=()
    if parse.arp()
    elif parse_lldp()
    call parse_arp()
    '''
    pass
