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
        # prepare variables
        dp = ev.msg.datapath
        dpid = dp.id
        ofproto = ev.msg.datapath.ofproto
        parser = ev.msg.datapath.ofproto_parser
        data = ev.msg.data
        match = ev.msg.match

        # create actions and update match
        mac_learning_action = self._mac_learning(dpid, data, ofproto, parser, match)

        # add flow
        actions = [mac_learning_action]
        self.add_flow(ev.msg.datapath, match, actions)

        # send packet
        out = parser.OFPPacketOut(datapath=dp, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ev.msg.match['in_port'], actions=actions, data=data)
        dp.send_msg(out)

    def _mac_learning(self, dpid, data, ofproto, parser, match):
        pkt = packet.Packet(data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        src = eth_pkt.src

        # learn address
        in_port = match['in_port']
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # get out_port
        dst = eth_pkt.dst
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # update match
        if out_port != ofproto.OFPP_FLOOD:
            match.set_in_port(in_port)
            match.set_eth_dst(dst)

        # create action
        return parser.OFPActionOutput(out_port)