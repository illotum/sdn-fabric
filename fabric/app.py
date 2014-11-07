"""
This module contains controller application to manage
a set of OpenFlow switches
"""
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3 as ofp
from ryu.ofproto import ofproto_v1_3_parser as parser

from fabric.network import Network
import fabric.packet as pkt
import fabric.flows as fl

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

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _handle_switch_features(self, ev):
        """
        Handle new switches connecting to the network.

        Feeds all port statuses to `self.net` and sends out LLDP discovery.

        TODO: Investigate if it is needed. Possibly better to handle
        switch state in `self._handle_state_change` and port state
        in `self._handle_port_status`.
        """
        pass

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _handle_state_change(self, ev):
        """
        Handle switch status change and initiates a round of LLDP discovery.

        Unlike OFPSwitchFeatures, this event doesn't carry ports state,
        but is fired also on switch going down.

        :param ev: datapath description and reason for state change
        :type ev: `ofp_event.EventOFPStateChange`,
                  where datapath can be None if negotiation didn't
                  end successfully.
        """
        pass

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, ev):
        """
        Parses incoming packet and calls a method that corresponds to dl_type.

        :param ev: packet contents and match structure to describe its
                   headers.
        :type ev: `ofp_event.EventOFPPacketIn`
        """

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _handle_port_status(self, ev):
        """
        Depending on `ev.msg.reason` adds or deletes port entry
        in `self.net` and starts another round of LLDP discovery.

        :param ev: port description and reason for state change
        :type ev: `ofp_event.EventOFPPortStatus`
        """

    def reply_to_arp(dp, pkt):
        """
        Responds to incoming ARP request using `self.net.mac_of` dict

        :param dp: datapath object that corresponds to originating switch
        :type dp: `ryu.controller.controller.Datapath`

        :param pkt: parsed eth and ARP headers of the request
        :type pkt: dict
        """
        pass

    def send_lldp(dp):
        """
        Sends LLDP broadcast from a given switch.

        :param dp: datapath object that corresponds to originating switch
        :type dp: `ryu.controller.controller.Datapath`
        """
        pass
