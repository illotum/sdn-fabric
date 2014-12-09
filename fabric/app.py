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
from ryu.ofproto import ether as ethertypes

from fabric.network import Network
import fabric.packet as packet
import fabric.flows as flows


IDLE_TIMEOUT = 10  #: Timeout for dynamic flows
DEF_PRI = 0
LOW_PRI = 1
HIGH_PRI = 2


class NetworkManager(app_manager.RyuApp):
    OFP_VERSIONS = [ofp.OFP_VERSION]

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
        dp = ev.datapath
        assert dp is not None
        if ev.state == MAIN_DISPATCHER:
            dp.send_msg(flows.flow_inbound(dp))
            dp.send_msg(flows.flow_to_transit(dp))
            dp.send_msg(flows.flow_default(dp, flows.T_DEFAULT, flows.T_LOCAL))
            dp.send_msg(flows.flow_default(dp, flows.T_LOCAL))
            self.run_discovery(dp)
            self.net.add_switch(dp.id)
        elif ev.state == DEAD_DISPATCHER:
            self.net.purge(dp.id)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, ev):
        """
        Parses incoming packet and calls a method that corresponds to dl_type.

        :param ev: packet contents and match structure to describe its
                   headers.
        :type ev: `ofp_event.EventOFPPacketIn`
        """
        msg = ev.msg
        dp = msg.datapath
        in_port = msg.match['in_port']

        headers = packet.parse(msg.data)
        if headers["ethertype"] == ethertypes.ETH_TYPE_LLDP:
            self.net.add_peer(dp.id, headers["peer_id"], in_port)
            if self.net.udl(dp.id, headers["peer_id"]):
                self.run_discovery(dp)
        elif (headers["ethertype"] == ethertypes.ETH_TYPE_ARP and
              headers["opcode"] == 1):
            pass

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

    def run_discovery(self, dp):
        """
        Sends LLDP broadcast from a given switch

        :param datapath: datapath object that corresponds to originating switch
        :type datapath: `ryu.controller.controller.Datapath`
        """
        pkt_lldp = packet.create_lldp(dp.id)
        msg = flows.send_packet_out(dp, pkt_lldp, ofp.OFPP_FLOOD)
        dp.send_msg(msg)
