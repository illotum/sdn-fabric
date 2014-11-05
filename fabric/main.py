from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3 as ofp
from ryu.ofproto import ofproto_v1_3_parser as parser
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import lldp

import fabric.config as conf
import fabric.topology as topo
import fabric.helpers as helpers

IDLE_TIMEOUT = 10
DEF_PRI, LOW_PRI, HIGH_PRI = 0, 1, 2
DEF_TABLE, TRANSIT_TABLE, EDGE_TABLE = 0, 1, 2

class NetworkManager(app_manager.RyuApp):
    OFP_VERSIONS = [ofp.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkManager, self).__init__(*args, **kwargs)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _handle_switch_features(self, ev):
        pass

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, ev):
        pass
