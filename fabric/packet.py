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
    pkt = packet.Packet()
    dst = 'FF:FF:FF:FF:FF:FF'
    ethertype = ether.ETH_TYPE_LLDP
    eth_pkt = ethernet.ethernet(dst, dpid, ethertype)
    pkt.add_protocol(eth_pkt)
    tlv_chassis_id = lldp.ChassisID(subtype=lldp.ChassisID.SUB_MAC_ADDRESS,
                                    chassis_id=haddr_to_bin(dpid))

    tlv_port_id = lldp.PortID(subtype=lldp.PortID.SUB_INTERFACE_NAME,
                              port_id=str(port_no))
    tlv_ttl = lldp.TTL(ttl=2)
    tlv_end = lldp.End()
    tlvs = (tlv_chassis_id, tlv_port_id, tlv_ttl, tlv_end)
    lldp_pkt = lldp.lldp(tlvs)
    pkt.add_protocol(lldp_pkt)
    pkt.serialize()
    
    

def create_arp( dl_src,dl_dst,nl_src,nl_dst):
    '''
    => ARP()
    '''
    pkt = packet.Packet()
    pkt.add_protocol(ethernet.ethernet(ethertype=pkt_eth.ethertype,
                                               dst=dl_dst,
                                               src=dl_src))
    pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                     src_mac=dl_src,
                                     src_ip= pkt_arp.nl_src,
                                     dst_mac=pkt_arp.dl_dst,
                                     dst_ip=pkt_arp.n1_dst))
    pkt.serialize()


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
