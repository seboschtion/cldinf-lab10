#!/usr/bin/python
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.cli import CLI

SPINES = []
LEAFS = []
SWITCH_PORTS = range(1, 10)
HOST_PORTS = range(10, 21)
LEAF_SWITCH_IDS = range(1, 1000)
SPINE_SWITCH_IDS = range(1000, 2000)

class Clos(Topo):
    """Clos topology example."""

    """Init.
        leaf: number of leaf switches
        spine: number of spine switches"""
    def __init__(self, leaf=3, spine=2):
        """Create custom topology."""
        self.net = Mininet(topo=None)
        self.controller = self.net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6633)

        # Initialize topology
        Topo.__init__(self)

        # Add leaf switches with hosts
        for leaf_nr in range(LEAF_SWITCH_IDS[0], leaf + 1):
            leaf_sw = self.net.addSwitch('l' + str(leaf_nr), failMode='secure', protocols='OpenFlow13')
            LEAFS.append(leaf_sw)
            host = self.net.addHost('h' + str(leaf_nr))
            self.net.addLink(leaf_sw, host, port1=HOST_PORTS[0], port2=1)

        # Add spine switches
        for spine_nr in range(1, spine + 1):
            spine_sw = self.net.addSwitch('s' + str(spine_nr + SPINE_SWITCH_IDS[0]), failMode='secure', protocols='OpenFlow13')
            SPINES.append(spine_sw)

        # addLink leafs to all spines
        i = 0
        for spine_link in SPINES:
            switch_port_number = SWITCH_PORTS[0]
            for leaf_link in LEAFS:
                self.net.addLink(spine_link, leaf_link, port1=switch_port_number, port2=switch_port_number + i)
                switch_port_number += 1
                i += 1

        self.controller.start()
        self.net.start()
        CLI(self.net)
        self.net.stop()

TOPOS = {'clos': (lambda leaf, spine: Clos(leaf, spine))}
