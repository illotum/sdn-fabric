"""
This module contains everything related to network topology processing
"""
import collections as coll
import heapq

Link = coll.namedtuple("Link", "dpid port_no")

class Network(object):
    """
    Container for all network state
    """

    def __init__():
        self.topo=TopologyDB()
        self.ip_to_mac={}
        self.mac_to_port= {} #for every MAC address=>{dpid,port_no}
        #Used to Update ports as given when a port event status changes

    def mac_of_ip(self, ip):
        """
        Returns mac of a given ip

        :param ip: 32b IP for a lookup
        :type ip: int

        :returns: 48b MAC
        :rtype: int
        """
        return self.ip_to_mac[ip]
        
    def port_of_mac(self,mac):
        """
        Returns dpid, port of a given Mac
        :param self: Self
        :type self: class object
        
        :param mac: mac address who's port no we wish to find
        :type mac: string
        
        :returns: integer port number
        :rtype: int
        """
        return self.mac_to_port[mac]
        
    def parse_ports(ports):
        self.topo[(dpid,port_no)]=(self._topo.P_LEARNING,None)
        pass

    def new_peer():
        pass

    def get_path(src_dpid,dst_dpid):
    #Gets the list of all the paths between core links
        pass


class TopologyDB(dict):

    P_EDGE=1
    P_CORE=2
    P_LEARNING=0
    """
    Topology graph with network related helpers
    """
    def spf():
        '''
        Returns nothing
        It stores a table of self_paths-> {(src,dst)=>[(dpid,port_no),(),()]}
        '''
        neighbourTable = self.neighbour_discovery(lsdb)
		for i in neighbourTable.keys():
			for j in neighbourTable.keys():
				if i is not j:
					self_paths[(i,j)]=shortestPath(neighbourTable,i,j)

    def get_all_core(self,lsdb,coreLinks=[]):
        """
        Returns all links in P_CORE state

        :returns: list of links
        :rtype: list of (dpid, port_no)
        """
        for x in  lsdb.keys():
	    if lsdb[x][0] is 2:
		coreLinks.append((x,lsdb[x][1]))
	return coreLinks
    
    def active_core_links(self,lsdb):
	activeLinks = {}
	for x in  lsdb.keys():
	    if lsdb[x][0] is 2:
		activeLinks[x] = lsdb[x][1]
        return activeLinks

    def neighbour_discovery(self,lsdb,topoTable={}):
	dlink = self.active_core_links(lsdb)
	for x,y in dlink.keys():
		if x not in topoTable:
			topoTable[x] = {dlink[(x,y)]:y}
		else:
			topoTable[x][dlink[(x,y)]] = y
	return topoTable

    def shortestPath(self,G,start,end):
	D,P = self.Dijkstra(G,start,end)
	Path = []
	while 1:
	    Path.append(end)
	    if end == start:
		break
	    end = P[end]
	Path.reverse()
	Path = self.path_to_port(Path,G)
	return Path

    def Dijkstra(self,G,start,end =None):
	D = {}	# dictionary of final distances
	P = {}	# dictionary of predecessors
	Q = PQDict()   # est.dist. of non-final vert.
	Q[start] = 0

	for v in Q:
	    D[v] = Q[v]
	    if v == end: break
			
	    for w in G[v]:
	        vwLength = D[v] + 1
		if w in D:
		    if vwLength < D[w]:
		        raise ValueError, \
	"Dijkstra: found better path to already-final vertex"
		elif (w not in Q) or (vwLength < Q[w]):
		    Q[w] = vwLength
		    P[w] = v
		
        return D,P

    def path_to_port(self,path,G,count=0):
	newPath= []
	while count < (len(path)-1):
	    src,dst = path[count],path[count+1]
	    newPath.append((src,G[src][dst]))
	    count+=1
	return newPath
		
        return [k for k,v in self.items() if v[0] == self.P_CORE]
