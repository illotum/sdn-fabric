## Edge
### Clients discovery
Collect MAC, IP, PORT, DPID for every client

### Reactive Local switching
 - If inbound (dl_type != PBB) and dl_dst is local
 - Out PORT
 
### Reactive ARP responder
 - If inbound (dl_dst == ff) and (dl_type == ARP) and (arp_opcode == request)
 - Craft ARP response from the controller
 - Out back

### Reactive Global switching
 - If inbound (dl_type != PBB) and dl_dst is not local
 - Push-PBB
 - Set ethernet type to 0x88e7
 - Set dl_dst destination switch
 
### Proactive Decapsulation
 - If inbound (dl_type == PBB) and dl_dst is switch_mac
 - Pop-PBB
 - GOTO Local switching

## Core
### Topology discovery
 - On switch_connected, or port_status
 - Send LLDP out
 - Expect a PacketIn
 - Store a link (reciever_dpid, reciever_port, sender, [sender_port])

### Best route calculation
 - Run SPF on links db
 - Produce a paths_dict { (src, dst) => [(id, port),...] }
 
### Procative rules installation
 - On any paths_dict change
 - Install rules for every (src, dst)
