from ex3_controllerbase import Ex3ControllerBase
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class Ex3FabricController(Ex3ControllerBase):
    def __init__(self, *args, **kwargs):
        super(Ex3FabricController, self).__init__(*args, **kwargs)
        self.mac_tables = {}

        # variables for easy topology adaptions
        self.switch_ports = range(1, 10)
        self.host_ports = range(10, 21)
        self.leaf_switch_ids = range(1, 1000)
        self.spine_switch_ids = range(1000, 2000)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        dp = ev.msg.datapath
        dpid = dp.id
        ofproto = dp.ofproto
        parser = dp.ofproto_parser
        data = ev.msg.data
        match = ev.msg.match

        # create actions and update match
        actions = self._flow_creation(dpid, ofproto, data, parser, match)

        # add flow
        self.add_flow(dp, match, actions)

        # send packet
        out = parser.OFPPacketOut(datapath=dp, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ev.msg.match['in_port'], actions=actions, data=data)
        dp.send_msg(out)

    def _flow_creation(self, dpid, ofproto, data, parser, match):
        # unpack packet
        pkt = packet.Packet(data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)

        # learn address
        in_port = match['in_port']
        self.mac_tables.setdefault(dpid, {})
        self.mac_tables[dpid][eth_pkt.src] = in_port

        # get out_ports
        out_ports = set()
        if self.__is_spine(dpid):
            # flood if spine
            out_ports.add(ofproto.OFPP_FLOOD)
        elif eth_pkt.dst in self.mac_tables[dpid]:
            # if address is known:
            #  - change match
            #  - set known port as out_port
            match.set_eth_dst(eth_pkt.dst)
            out_ports.add(self.mac_tables[dpid][eth_pkt.dst])
        elif in_port in self.host_ports:
            # flood if from host
            out_ports.add(ofproto.OFPP_FLOOD)
        elif in_port in self.switch_ports:
            # flood only to host ports
            out_ports = self.host_ports

        # create action for every out_port
        actions = []
        for out_port in out_ports:
            self.logger.info(" # add flow for switch %s: out_port is %s when in_port is %s", dpid, out_port, match['in_port'])
            actions.append(parser.OFPActionOutput(out_port))

        return actions

    def __is_spine(self, dpid):
        return dpid in self.spine_switch_ids
