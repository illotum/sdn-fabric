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
	
	self.lsdb={}
	
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _handle_switch_features(self, ev):
        """
        Handle new switches connecting to the network, their ports
        and initiates a round of LLDP discovery.

        Feeds all port statuses to `self.net` and sends out LLDP discovery.

        TODO: Investigate if it is needed. Possibly better to handle
        switch state in `self._handle_state_change` and port state
        in `self._handle_port_status`

        """
        msg = ev.msg
        datapath=msg.datapath
    	dict_key=msg.ports.keys()
	dict_key.remove(65534)
	
	for key in dict_key:
            
	    self.features_dict[(msg.datapath_id,key)]=(msg.ports[key].state,msg.ports[key].hw_addr)
	    
	self.send_lldp(datapath)
	

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
        del switch_connected[ev.datapath] 
        for key in switch_connected: 
            self.send_lldp(key)

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
	   self.lsdb[(descr["dpid_src"],descr["port_src"])]=(2,descr["dpid_dst"])

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _handle_port_status(self, ev):
        """
        Depending on `ev.msg.reason` adds or deletes port entry
        in `self.net` and starts another round of LLDP discovery.

        :param ev: port description and reason for state change
        :type ev: `ofp_event.EventOFPPortStatus`
        """
        msg = ev.msg
        datapath=msg.datapath
        reason = msg.reason
        port_no = msg.desc.port_no
        
        if reason == ofp.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
            #Will flood an LLDP message from every switch connected (switch_features maintains this list). Packet_IN will handle the rest (will add it to the database)
            for switch in self.switch_connected:
            	send_lldp(datapath) 
            	
        elif reason == ofp.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
            # del self.lsdb[]
            
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)

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
        Sends LLDP broadcast from a given switch

        :param datapath: datapath object that corresponds to originating switch
        :type datapath: `ryu.controller.controller.Datapath`

        
        """

    	pkt_lldp=pack.create_lldp(datapath.id)
    	msg=fl.send_out_packet(datapath,pkt_lldp,ofp.OFPP_FLOOD)
    	datapath.send_msg(msg)
    	
    def send_lldp_all():
        """
        Sends LLDP broadcast to all switches that are registered on the controller
                
        """
        for switch in self.switch_connected.keys(): # Every key is a DPID of the switch registered on the controller
        	send_lldp(self.switch_connected[switch]) # Sending (flood) an LLDP packet for aech switch in the list. "self.switch_connected[switch]" returns a datapath object
    	
    
