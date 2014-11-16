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
from ryu.lib.mac import haddr_to_bin

from fabric.network import Network
import fabric.packet as pack
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

	self.features_dict={}
	self.features_dict_intermediate={}
	self.lsdb={}
	
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _handle_switch_features(self, ev):
        """
        Handle new switches connecting to the network, their ports
        and initiates a round of LLDP discovery.

        Feeds all port statuses to `self.net` and sends out LLDP discovery.

        TODO: Investigate if it is needed. Possibly better to handle
        switch state in `self._handle_state_change` and port state
        in `self._handle_port_status`.

        """
        msg = ev.msg
    	dict_key=msg.ports.keys()
	dict_key.remove(65534)
	print dict_key
	self.features_dict[msg.datapath_id]=""
	print self.features_dict
	for key in dict_key:
            
	    self.features_dict_intermediate[key]=[msg.ports[key].port_no,msg.ports[key].hw_addr,msg.ports[key].state]
	    print self.features_dict_intermediate
	    
	self.features_dict[msg.datapath_id]=self.features_dict_intermediate
	print self.features_dict
	

    @set_ev_cls(ofp_event.EventOFPStateChange, [DEAD_DISPATCHER])
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
        pass

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, ev):
        """
        Parses incoming packet and calls a method that corresponds to dl_type.

        :param ev: packet contents and match structure to describe its
                   headers.
        :type ev: `ofp_event.EventOFPPacketIn`
        """
        msg=ev.msg
        pkt=packet.Packet(msg.data)
        datapath=msg.datapath
        in_port=msg.in_port
        descr=pack.parse(msg.data,datapath.id,in_port)
        
        pkt_arp=pkt.get_protocol(arp.arp)
        if pkt_arp:
            descr=pack.parse_arp(descr,msg.data)
	    key=descr["nl_dst"]
	    if key in self.net.ip_to_mac:
	    	dl_dst=self.net.ip_to_mac[key]
		arp_dict={"nl_src":descr["nl_src"],"nl_dst":descr["nl_dst"],"dl_src":descr["dl_src"],"dl_dst":dl_dst}
		self.reply_to_arp(datapath.id,arp_dict)
		return
	
	self.net.mac_to_port[descr["dl_src"]]=msg.in_port
        
        dst=descr["dl_dst"]
        if dst in self.net.mac_to_port:
            out_port=self.net.mac_to_port[dst]
        else:
            out_port=ofp.OFPP_FLOOD

        actions=[datapath.ofproto_parser.OFPActionOutput(out_port)] 

        # install a flow to avoid packet_in next time
        if out_port != ofp.OFPP_FLOOD:
            self.add_flow(datapath, msg.in_port, dst, actions)
	   
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,actions=actions)
	datapath.send_msg(out)

        
        pkt_lldp=pkt.get_protocol(lldp.lldp)
        if pkt_lldp:
           descr=pack.parse_lldp(descr,msg.data)
	   self.lsdb[(descr["dpid_dst"],descr["port_src"])]=(2,descr["dpid_src"])

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _handle_port_status(self, ev):
        """
        Depending on `ev.msg.reason` adds or deletes port entry
        in `self.net` and starts another round of LLDP discovery.

        :param ev: port description and reason for state change
        :type ev: `ofp_event.EventOFPPortStatus`
        """
        pass

    def reply_to_arp(dp, pkt):
        """
        Responds to incoming ARP request using `self.net.mac_of` dict

        :param dp: datapath object that corresponds to originating switch
        :type dp: `ryu.controller.controller.Datapath`

        :param pkt: parsed eth and ARP headers of the request
        :type pkt: dict
        """
        dl_dst, nl_dst, nl_src = pkt["dl_src"], pkt["nl_src"],pkt["nl_dst"]
        dl_src = self.net.mac_of[nl_src]
        out_port = dp.ofproto.OFPP_LOCAL

        pkt = create_arp( dl_src,dl_dst,nl_src,nl_dst)

        send_out_packet(dp,pkt,out_port)



    def send_lldp(datapath):
        """
        Sends LLDP broadcast from a given switch.

        :param datapath: datapath object that corresponds to originating switch
        :type datapath: `ryu.controller.controller.Datapath`

        
        """

    	pkt_lldp=pack.create_lldp(datapath.id)
    	msg=fl.send_out_packet(datapath,pkt_lldp,ofp.OFPP_FLOOD)
    	datapath.send_msg(msg)
    	
    	
    def add_flow(self, datapath, in_port, dst, actions):
        

        match = datapath.ofproto_parser.OFPMatch(
            in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofp.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofp.OFP_DEFAULT_PRIORITY,
            flags=ofp.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)	
