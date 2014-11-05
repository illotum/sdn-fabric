#!/bin/env python

def instructions(actions=None, goto=None):
    # Compose instructions set from given entries
    inst = []
    if actions:
        inst.append(
            parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                            actions))
    if goto:
        inst.append(parser.OFPInstructionGoto(goto))

    return inst

