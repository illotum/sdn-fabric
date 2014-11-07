"""
This module containes pure functions to help with
creating flow table entries.
"""

from ryu.ofproto import ofproto_v1_3 as ofp
from ryu.ofproto import ofproto_v1_3_parser as parser

def compose(actions=[], to_table=0):
    """
    Compose instructions set from given entries

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
        inst.append(parser.OFPInstructionGoto(to_table))

    return inst

def dpid_to_mac(dpid):
    pass
def flow_to_port(dl_dst,out_port,tableno=DEFAULT_TABLE_SOMETHING):
    '''
    =>parser.OFPFlowMod
    '''
    pass

def flow_to_remote(dl_dst,dpid):
    pass

def to_local():
    '''
    returns to_port(,,LOCAL---can be anything)
    '''
    pass
def match_all():
    '''
    =>Match
    3.
    '''
    pass

def flow_install_transit():
    '''
    => FlowMod
    2.
    '''
    pass


def match_inbound(dpid):
    '''
    => FLOWMOD
    1.
    '''
    pass


