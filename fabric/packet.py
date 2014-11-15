"""
This module containes pure functions to parse and craft packets.
"""

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import lldp
from ryu.ofproto import ether
from ryu.lib.mac import haddr_to_bin


def create_lldp(dpid, port_no=1):
    '''
    Creates an LLDP broadcast packet

    :param dpid: 64bit switch id
    :type dpid: int

    :param port_no: port number
    :type port_no: int

    :returns: binary representation of LLDP packet
    :rtype: `bytearray`
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
    data = pkt.data
    return data


def create_arp( dl_src,dl_dst,nl_src,nl_dst):
    '''
    Creates an ARP reply packet

    :param dl_src: 48bit MAC address
    :type dl_src: int

    :param dl_dst: 48bit MAC address
    :type dl_dst: int

    :param nl_src: 32bit IP address
    :type nl_src: int

    :param nl_dst: 32bit IP address
    :type nl_dst: int

    :returns: binary representation of ARP packet
    :rtype: `bytearray`
    '''
    pkt = packet.Packet()
    pkt.add_protocol(ethernet.ethernet(ethertype=pkt_eth.ethertype,
                                               dst=dl_dst,
                                               src=dl_src))
    pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                     src_mac=dl_src,
                                     src_ip=nl_src,
                                     dst_mac=dl_dst,
                                     dst_ip=n1_dst))
    pkt.serialize()
    return pkt


def parse_lldp(descr,data):
    '''
    Parses LLDP headers and adds them to provided dict

    :param data: binary of a packet to parse
    :type data: bitearray

    :param headers: parsed headers
    :type headers: dict

    :returns: `headers` with additional entries
              of "dpid" and "port_no" form LLDP
    :rtype: dict
    '''
    
    pkt = packet.Packet(data)
    pkt_lldp = pkt.get_protocol(lldp.lldp)
    s = str(pkt_lldp.tlvs[0].chassis_id)
    dpid_dst = struct.unpack("!Q",'\x00\x00' + s)[0]
    
    descr["dpid_dst"] = dpid_dst
    
    return descr


def parse_arp(descr,data):
    '''
    Parses ARP headers and adds them to provided dict

    :param data: binary of a packet to parse
    :type data: bitearray

    :param headers: parsed headers
    :type headers: dict

    :returns: `headers` with additional entries of "opcode", "nl_src"
              and "nl_dst" form ARP.
              Entries from the Ethernet frame, "dl_src" and "dl_dst",
              are NOT overwritten.
    :rtype: dict
    '''
    pkt = packet.Packet(data)
    pkt_arp = pkt.get_protocol(arp.arp)
    
    descr["nl_src"] = pkt_arp.src_ip
    descr["nl_dst"] = pkt_arp.dst_ip
    descr["opcode"] = pkt_arp.opcode
    
    return descr


def parse(data, dpid_src, port_src):
    '''
    Parses Ethernet headers and calls for additional parsing
    in case of ARP and LLDP.

    :param data: binary of a packet to parse
    :type data: bitearray

    :returns: dictionary of all important headers parsed
              with "dl_src" and "dl_dst" at minimum.
    :rtype: dict
    '''
    descr = { "dpid_src" : '', "port_src" : '', "dl_src" : '', "dl_dst" : '' , "nl_src" : '', "nl_dst" : '' , "dpid_dst" : '' , "opcode" : '' , "ethertype" : ''}
    descr["dpid_src"] = dpid_src
    descr["port_src"] = port_src
    
    pkt = packet.Packet(data)
    pkt_eth = pkt.get_protocol(ethernet.ethernet)
    
    desrc["dl_src"] = pkt_eth.src
    descr["dl_dst"] = pkt_eth.dst
    
    return descr
   
