"""
This module containes pure functions to parse and craft packets.
"""

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import lldp
from ryu.ofproto import ether
from ryu.lib.mac import haddr_to_bin

import struct


def create_lldp(dpid, port_no=1):  #Default Port_no is 1 as we are flooding lldp packets
    '''
    Creates an LLDP broadcast packet

    :param dpid: 64bit switch id
    :type dpid: int

    :param port_no: port number
    :type port_no: int

    :returns: binary representation of LLDP packet
    :rtype: `bytearray`
    '''

    pkt = packet.Packet()           # creating empty pkt
    dst = 'FF:FF:FF:FF:FF:FF'
    ethertype = ether.ETH_TYPE_LLDP
    eth_pkt = ethernet.ethernet(dst, dpid, ethertype)  
    pkt.add_protocol(eth_pkt)      # Adding Ethernet 
    tlv_chassis_id = lldp.ChassisID(subtype=lldp.ChassisID.SUB_MAC_ADDRESS,
                                    chassis_id=haddr_to_bin(dpid))

    tlv_port_id = lldp.PortID(subtype=lldp.PortID.SUB_INTERFACE_NAME,
                              port_id=str(port_no))
    tlv_ttl = lldp.TTL(ttl=2)
    tlv_end = lldp.End()
    tlvs = (tlv_chassis_id, tlv_port_id, tlv_ttl, tlv_end)
    lldp_pkt = lldp.lldp(tlvs)
    pkt.add_protocol(lldp_pkt)   #Adding llDP
    pkt.serialize()             # Converting into 'bytearray'
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
    pkt.add_protocol(ethernet.ethernet(ethertype=2054,          #Ethertype 2054 is for ARP 
                                               dst=dl_dst,
                                               src=dl_src))
    pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                     src_mac=dl_src,
                                     src_ip=nl_src,
                                     dst_mac=dl_dst,
                                     dst_ip=nl_dst))
    pkt.serialize()
    return pkt


def parse_lldp(descr,data):
    '''
    Parses LLDP headers and adds them to provided dict
    
    dpid_dst: Switch who sent(flood) lldp packet
    

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
    
    dpid_src: switch from which controller received packet
    port_src: switch port on which packet was received
    dl_src: Data link layer source address (MAC)
    dl_dst: Data link layer destination address (MAC)
    nl_src: Network layer source address (IP)
    nl_dst: Network layer destination address (IP)
    opcode: int :Define type of ARP Request or Reply
    ethertype: int : Define type of protocol (ARP or LLDP)
    '''
    descr = { "dpid_src" : '', "port_src" : '', "dl_src" : '', "dl_dst" : '' , "nl_src" : '', "nl_dst" : '' , "dpid_dst" : '' , "opcode" : '' , "ethertype" : ''}
    descr["dpid_src"] = dpid_src
    descr["port_src"] = port_src
    
    pkt = packet.Packet(data)
    pkt_eth = pkt.get_protocol(ethernet.ethernet)
    
    descr["dl_src"] = pkt_eth.src
    descr["dl_dst"] = pkt_eth.dst
    descr["ethertype"] = pkt_eth.opcode
    
    if descr["ethertype"] == 2054:            # If packet is ARP
        descr=parse_arp(descr,data)
    
    elif descr["ethertype"] == 35020:       # If packet is LLDP
        descr=parse_lldp(descr,data)
    
    return descr
   
