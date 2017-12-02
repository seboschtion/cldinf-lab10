from ex3_controllerbase import Ex3ControllerBase
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

class Ex3FabricController(Ex3ControllerBase):
    def __init__(self, *args, **kwargs):
        super(Ex3FabricController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        mac_learning_tuple = self.mac_learning(ev.msg)

        match = mac_learning_tuple[0]
        actions = [mac_learning_tuple[1]]
        self.add_flow(ev.msg.datapath, match, actions)

        out = ev.msg.datapath.ofproto_parser.OFPPacketOut(datapath=ev.msg.datapath,
                                  buffer_id=ev.msg.datapath.ofproto.OFP_NO_BUFFER,
                                  in_port=ev.msg.match['in_port'], actions=actions,
                                  data=ev.msg.data)
        ev.msg.datapath.send_msg(out)

    def mac_learning(self, msg):
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        src = eth_pkt.src

        # learn address
        in_port = msg.match['in_port']
        self.mac_to_port.setdefault(msg.datapath.id, {})
        self.mac_to_port[msg.datapath.id][src] = in_port

        # get out_port
        dst = eth_pkt.dst
        if dst in self.mac_to_port[msg.datapath.id]:
            out_port = self.mac_to_port[msg.datapath.id][dst]
        else:
            out_port = msg.datapath.ofproto.OFPP_FLOOD

        # create match
        match = msg.datapath.ofproto_parser.OFPMatch()
        if out_port != msg.datapath.ofproto.OFPP_FLOOD:
            match.set_in_port(in_port)
            match.set_eth_dst(dst)

        # create action
        action = msg.datapath.ofproto_parser.OFPActionOutput(out_port)

        return (match, action)