"""
This module containes pure functions to help with creating flow table entries.

No to switch communication is supposed to reside in here.
"""

from ryu.ofproto import ofproto_v1_4 as ofp
from ryu.ofproto import ofproto_v1_4_parser as parser
from ryu.lib.ofctl_v1_3 import actions_to_str
import netaddr
T_DEFAULT = 0
T_TRANSIT = 1
T_LOCAL = 2
P_DEFAULT = 0
P_LOW = 10
P_HIGH = 20


class _ryu_dialect(netaddr.mac_unix):
    word_fmt = '%.2x'


def compose(actions=[], to_table=0):
    """
    Compose instructions set from given entries.

    :param actions: actions to perform after match
    :type actions: list of `parser.OFPAction`

    :param to_table: table to switch to after applying all actions;
                     value 0 (default table) will be ignored
    :type to_table: int

    :returns: instructions for `parser.OFPFlowMod`
    :rtype: list of `parser.OFPInstruction`
    """
    inst = []
    if actions:
        inst.append(
            parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                         actions))
    if to_table:
        inst.append(parser.OFPInstructionGotoTable(to_table))
    return inst


def int_to_mac(dpid):
    """
    Cut only lowest 48 bits of an integer and transform it to string.

    :param dpid: 64bits of switch id
    :type dpid: int

    :returns: MAC address
    :rtype: str
    """
    mac_addr = dpid & (2 ** 48 - 1)
    return str(netaddr.EUI(mac_addr, version=48, dialect=_ryu_dialect))


def flow_to_port(dp, dl_dst, out_port, table=T_LOCAL):
    '''
    Create a FlowMod structure that matches destination MAC and
    sends packet out of a port.

    By default it is used for local switching, but table may be set to
    `fabric.flow.T_TRANSIT` for transit rules.

    :param dp: switch description
    :type dp: `ryu.controller.controller.Datapath`

    :param dl_dst: destination MAC address
    :type dl_dst: str

    :param out_port: output port
    :type out_port: int

    :param table: flow table to install this rule in
    :type table: int

    :returns: FlowMod to send to the switch
    :rtype: `parser.OFPFlowMod`
    '''

    inst = compose([parser.OFPActionOutput(out_port)])
    msg = parser.OFPFlowMod(datapath=dp,
                            priority=P_LOW,
                            match=parser.OFPmatch(eth_dst=dl_dst),
                            instructions=inst,
                            table_id=table)

    return msg


def flow_to_remote(dp, dl_dst, dpid):
    '''
    Create a FlowMod structure that matches destination MAC and
    encapsulates frame in PBB before switching to a TRANSIT table.

    :param dp: switch description
    :type dp: `ryu.controller.controller.Datapath`

    :param dl_dst: destination MAC address
    :type dl_dst: str

    :param dpid: destination switch id to be set as dl_dst after encapsulation
    :type out_port: int

    :returns: FlowMod to send to the switch
    :rtype: `parser.OFPFlowMod`
    '''
    switch_mac = int_to_mac(dpid)
    actions = [
        parser.OFPActionPushPbb(0x88E7),
        parser.OFPActionSetField(eth_dst=switch_mac)
        ]

    msg = parser.OFPFlowMod(datapath=dp,
                            match=parser.OFPmatch(eth_dst=dl_dst),
                            instructions=compose(actions, to_table=T_TRANSIT),
                            table_id=T_LOCAL)
    return msg


def flow_default(dp, table, to_table=0):

    '''
    Produce an default rule that will be matching anything before applying an
    action and/or switching table.

    Default behaviour is to send traffic to the controller, but if to_table
    is provided it will be switch to that table instead.

    :param dp: datapath description
    :type dp: `ryu.controller.controller.Datapath`

    :param table: flow table to install this rule in
    :type table: int

    :param to_table: flow table to switch traffic to
    :type to_table: int

    :return: message to send to the switch
    :type: `parser.OFPFlowMod`
    '''
    if to_table:
        actions = []
    else:
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]

    match = parser.OFPMatch()
    msg = parser.OFPFlowMod(datapath=dp,
                            priority=P_DEFAULT,
                            table_id=table,
                            match=match,
                            instructions=compose(actions, to_table))
    return msg


def flow_to_transit(dp):
    '''
    Create a FlowMod structure that matches PBB packets and switches
    them to TRANSIT table.

    :param dp: datapath description
    :type dp: `ryu.controller.controller.Datapath`
    '''
    msg = parser.OFPFlowMod(datapath=dp,
                            priority=P_LOW,
                            table_id=T_DEFAULT,
                            match=parser.OFPMatch(eth_type=0x88E7),
                            instructions=compose(to_table=T_TRANSIT))

    return msg


def flow_inbound(dp):
    '''
    Produce a FlowMod that matches PBB encapsulated flows
    destined to this switch and decapsulates them before switching
    to LOCAL table

    :param dp: datapath description
    :type dp: `ryu.controller.controller.Datapath`

    :returns: flow mod message
    :rtype: `parser.OFPFlowMod`
    '''
    switch_mac = int_to_mac(dp.id)
    match = parser.OFPMatch(eth_type=0x88E7, eth_dst=switch_mac)
    actions = [parser.OFPActionPopPbb()]
    msg = parser.OFPFlowMod(datapath=dp,
                            priority=P_HIGH,
                            table_id=T_DEFAULT,
                            match=match,
                            instructions=compose(actions, to_table=T_LOCAL))
    return msg


def send_packet_out(dp, pkt, out_port, in_port=ofp.OFPP_CONTROLLER):
    """
    Produce a message for a switch to send the provided
    packet out.

    :param dp: datapath description
    :type dp: `ryu.controller.controller.Datapath`

    :param pkt: packet contents in serialized format
    :type pkt: `bytearray`

    :param out_port: switch port to send packet out of
    :type out_port: int

    :param in_port: inbount port for packets that were recieved
                    by this switch; defaults to `ofp.OFPP_CONTROLLER`
    :type in_port: int

    :returns: message to be sent to switch
    :rtype: `parser.OFPPacketOut`
    """
    actions = [parser.OFPActionOutput(out_port)]
    msg = parser.OFPPacketOut(datapath=dp,
                              buffer_id=ofp.OFP_NO_BUFFER,
                              in_port=in_port,
                              actions=actions,
                              data=pkt)
    return msg
