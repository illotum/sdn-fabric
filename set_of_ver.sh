#!/bin/sh

for i in $(seq $2); do
	 sudo ovs-vsctl set bridge s$i protocols=OpenFlow1$1
done
