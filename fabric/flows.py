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

def action_to_local():
    pass

def action_to_remote():
    pass

def action_decapsulate():
    pass

def match_all():
    pass

def match_transit():
    pass

def match_inbound(dpid):
    pass


