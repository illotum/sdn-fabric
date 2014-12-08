"""
This module contains controller application to manage
a set of OpenFlow switches
"""
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4 as ofp
from ryu.ofproto import ofproto_v1_4_parser as parser

from fabric.network import Network
import fabric.packet as packet
import fabric.flows as flows


IDLE_TIMEOUT = 10  #: Timeout for dynamic flows
DEF_PRI = 0
LOW_PRI = 1
HIGH_PRI = 2


class NetworkManager(app_manager.RyuApp):

    """
    Core class of this package, NetworkManager is a top-level Ryu application
    """

    def __init__(self, *args, **kwargs):
        super(NetworkManager, self).__init__(*args, **kwargs)
        self.net = Network()  #: Init the Network instance

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _handle_state_change(self, ev):
        """
        Handle switch going down and performs a topology update.

        Unlike OFPSwitchFeatures, this event doesn't carry ports state,
        but is fired also on switch going down.

        :param ev: datapath description and reason for state change
        :type ev: `ofp_event.EventOFPStateChange`,
                  where datapath can be None if negotiation didn't
                  end successfully.
        """
        datapath = ev.datapath
        assert datapath is not None
        if ev.state == MAIN_DISPATCHER:
            self.run_discovery(datapath)
        elif ev.state == DEAD_DISPATCHER:
            self.net.purge(datapath.id)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, ev):
        """
        Parses incoming packet and calls a method that corresponds to dl_type.

        :param ev: packet contents and match structure to describe its
                   headers.
        :type ev: `ofp_event.EventOFPPacketIn`
        """
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        # calls parse function and stores packet data in descr
        descr = packet.parse(msg.data, datapath.id, in_port)
        print("PACKET IN FROM " + ev.msg.datapath.id)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _handle_port_status(self, ev):
        """
        Depending on `ev.msg.reason` adds or deletes port entry
        in `self.net` and starts another round of LLDP discovery.

        :param ev: port description and reason for state change
        :type ev: `ofp_event.EventOFPPortStatus`
        """
        msg = ev.msg
        port_no = msg.desc.port_no
        state = msg.desc.state
        dpid = msg.datapath.id

        # port.state == 1 for link down and 0 for link up
        if msg.reason == ofp.OFPPR_DELETE or state:
            self.net.purge(dpid, port_no)
        else:
            self.run_discovery(msg.datapath)

    def reply_to_arp(self, dp, pkt):
        """
        Responds to incoming ARP request using `self.net.mac_of` dict

        :param dp: datapath object that corresponds to originating switch
        :type dp: `ryu.controller.controller.Datapath`

        :param pkt: parsed eth and ARP headers of the request
        :type pkt: dict
        """
        dl_dst, nl_dst, nl_src = pkt["dl_src"], pkt["nl_src"], pkt["nl_dst"]
        dl_src = self.net.ip_to_mac[nl_src]
        out_port = dp.ofproto.OFPP_LOCAL

        pkt = packet.create_arp(dl_src, dl_dst, nl_src, nl_dst)

        flows.send_out_packet(dp, pkt, out_port)

    def run_discovery(self, datapath):
        """
        Sends LLDP broadcast from a given switch

        :param datapath: datapath object that corresponds to originating switch
        :type datapath: `ryu.controller.controller.Datapath`
        """
        print("DISCOVERY FOR " + str(datapath.id))
        pkt_lldp = packet.create_lldp(datapath.id)
        msg = flows.send_packet_out(datapath, pkt_lldp, ofp.OFPP_FLOOD)
        datapath.send_msg(msg)
