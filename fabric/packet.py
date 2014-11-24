"""
This module contains pure functions to parse and craft packets.
"""

from ryu.ofproto import ofproto_v1_4 as ofp
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import lldp
from ryu.ofproto import ether as ethertypes
import fabric.flows as fl


def create_lldp(dpid, port_no=ofp.OFPP_FLOOD):
    '''
    Create an LLDP broadcast packet.

    :param dpid: 64bit switch id
    :type dpid: int

    :param port_no: port number
    :type port_no: int

    :returns: binary representation of LLDP packet
    :rtype: `bytearray`
    '''

    pkt = packet.Packet()  # creating empty pkt
    dst, src = lldp.LLDP_MAC_NEAREST_BRIDGE  # Singlehop LLDP multicast
    src = fl.int_to_mac(dpid)
    ethertype = ethertypes.ETH_TYPE_LLDP
    eth_pkt = ethernet.ethernet(dst, src, ethertype)
    pkt.add_protocol(eth_pkt)  # Adding Ethernet
    tlvs = (lldp.ChassisID(subtype=lldp.ChassisID.SUB_LOCALLY_ASSIGNED,
                           chassis_id=hex(dpid)),
            lldp.PortID(subtype=lldp.PortID.SUB_INTERFACE_NAME,
                        port_id=hex(port_no)),
            lldp.TTL(1),
            lldp.End())
    lldp_pkt = lldp.lldp(tlvs)
    pkt.add_protocol(lldp_pkt)  # Adding llDP
    return pkt.serialize()


def create_arp(dl_src, dl_dst, nl_src, nl_dst):
    '''
    Create an ARP reply packet.

    :param dl_src: 48bit MAC address
    :type dl_src: str

    :param dl_dst: 48bit MAC address
    :type dl_dst: str

    :param nl_src: 32bit IP address
    :type nl_src: str

    :param nl_dst: 32bit IP address
    :type nl_dst: str

    :returns: binary representation of ARP packet
    :rtype: `bytearray`
    '''
    pkt = packet.Packet()
    pkt.add_protocol(ethernet.ethernet(ethertype=ethertypes.ETH_TYPE_ARP,
                                       dst=dl_dst,
                                       src=dl_src))
    pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                             src_mac=dl_src,
                             src_ip=nl_src,
                             dst_mac=dl_dst,
                             dst_ip=nl_dst))
    return pkt.serialize()


def parse_lldp(data):
    '''
    Parse LLDP headers and adds them to provided dict.

    :param data: binary of a packet to parse
    :type data: `bytearray`

    :returns: `headers` with additional entries of "peer_id"
              and "peer_port" form LLDP
    :rtype: dict
    '''

    pkt = packet.Packet(data)
    pkt_lldp = pkt.get_protocol(lldp.lldp)

    headers = {"peer_id": int(pkt_lldp.tlvs[0].chassis_id, 16),
               "peer_port": int(pkt_lldp.tlvs[1].port_id, 16)}

    return headers


def parse_arp(data):
    '''
    Parse ARP headers and add them to provided dict.

    :param data: binary of a packet to parse
    :type data: `bytearray`

    :returns: `headers` with entries of "opcode", "nl_src" and "nl_dst"
              from ARP.
    :rtype: dict
    '''
    pkt = packet.Packet(data)
    pkt_arp = pkt.get_protocol(arp.arp)

    headers = {"nl_src": pkt_arp.src_ip,
               "nl_dst": pkt_arp.dst_ip,
               "opcode": pkt_arp.opcode}

    return headers


def parse(data):
    '''
    Parse Ethernet headers and calls for additional parsing
    in case of ARP and LLDP.

    :param data: binary of a packet to parse
    :type data: `bytearray`

    :returns: dictionary of all important headers parsed
              with "dl_src" and "dl_dst" and "ethertype" at minimum;
    :rtype: dict
    '''
    pkt = packet.Packet(data)
    pkt_eth = pkt.get_protocol(ethernet.ethernet)

    headers = {"dl_src": pkt_eth.src,
               "dl_dst": pkt_eth.dst,
               "ethertype": pkt_eth.ethertype}

    if headers["ethertype"] == ethertypes.ETH_TYPE_ARP:
        headers += parse_arp(data)
    elif headers["ethertype"] == ethertypes.ETH_TYPE_ARP:
        headers += parse_lldp(data)

    return headers
