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
from fabric.network import TopologyDB as topo
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

	self.port_list={}
	self.switch_connected={}
	self.lsdb={}
	self.features_dict={}
	
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
        fl.install_default_flow(datapath)  # installs default flows for openflow 1.4
        port_list=msg.ports.keys()         # gets the list of ports from msg.ports dictionary
        port_list.remove(65534)            # removes the port connected to controller
        self.switch_connected[datapath.id]=datapath  # stores datapath id as key and datapath object as value
         
        #stores port details in features_dict dictionary. 0 means learning state.
        for key in port_list: 
        	self.features_dict[(msg.datapath_id,key)]=(0,msg.ports[key].hw_addr)
        # sends lldp packets to all connected switches
	for key in self.switch_connected: 
		self.send_lldp(self.switch_connected[key])
	

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
        # deletes disconnected switch and sends lldp to every connected switch.
        del switch_connected[ev.datapath] 
        for key in switch_connected: 
            self.send_lldp(key)
            
        new_topology=self.topo.spf(self.lsbd)    # udpates the topology

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
        in_port=msg.match['in_port']
        descr=pack.parse(msg.data,datapath.id,in_port) # calls parse function and stores packet data in descr
        
        pkt_arp=pkt.get_protocol(arp.arp) # checks for arp packet
        if pkt_arp:
            descr=pack.parse_arp(descr,msg.data) # calls parse_arp function to get source and destination ip addresses
	    
            self.net.ip_to_mac[descr["nl_src"]]=descr["dl_src"] # saves ip to mac entry in ip_to_mac dictionary
            # mac_to_port format = {dpid:{mac-address:in_port}}
	    self.net.mac_to_port.setdefault(datapath.id, {})
             
            
            key=descr["nl_dst"]
	    if key in self.net.ip_to_mac:
	    	dl_dst=self.net.ip_to_mac[key]
		arp_dict={"nl_src":descr["nl_src"],"nl_dst":descr["nl_dst"],"dl_src":descr["dl_src"],"dl_dst":dl_dst}
		self.reply_to_arp(datapath.id,arp_dict)
		return
	
	
        
        dst=descr["dl_src"]
        self.net.mac_to_port[datapath.id][dst] = in_port # saves mac to port entry in mac_to_port dictionary

        if dst in self.net.mac_to_port[datapath.id]:
            out_port = self.net.mac_to_port[datapath.id][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions=[datapath.ofproto_parser.OFPActionOutput(out_port)] 

        # install a flow to avoid packet_in next time
        if out_port != ofp.OFPP_FLOOD:
            fl.add_flow(datapath, msg.in_port, dst, actions)
	   
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,actions=actions)
	datapath.send_msg(out)

        # lldp packet parsing
        pkt_lldp=pkt.get_protocol(lldp.lldp)
        if pkt_lldp:
            descr=pack.parse_lldp(descr,msg.data)
            self.lsdb[(descr["dpid_src"],descr["port_src"])]=(2,descr["dpid_dst"]) # 2 refers to core switches
	    try:
	    	new_topology=self.topo.spf(self.lsbd)
	    except:
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
        datapath=msg.datapath
        dpid = datapath.id
        reason = msg.reason
        port_no = msg.desc.port_no
        
        if reason == ofp.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
            send_lldp_all() #Will flood an LLDP message from every switch connected (switch_features maintains this list). Packet_IN will handle the rest (will add it to the database)

        elif reason == ofp.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
            
            port_type = lsdb[(dpid, port_no)][0] #Getting a type of the port that went down
            
            if port_type == 2: #If the port is a core port or a learning
                del lsdb[dpid, port_no] # Deleting this port from the lsdb database
                send_lldp_all() #Will flood an LLDP message from every switch connected in order to discover the topology again

            elif port_type == 1:
                del lsdb[dpid, port_no] # Deleting this port from the lsdb database. Since this is an EDGE port we don't need to fire another round of LLDP

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
        dl_src = self.net.ip_to_mac[nl_src]
        out_port = dp.ofproto.OFPP_LOCAL

        pkt = create_arp( dl_src,dl_dst,nl_src,nl_dst)

        fl.send_out_packet(dp,pkt,out_port)



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
    	
    
