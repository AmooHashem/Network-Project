from json import JSONEncoder


class Packet:
    def __init__(self, type, src_id, dst_id, data):
        self.type = type
        self.src_id = src_id
        self.dst_id = dst_id
        self.data = data


class PacketEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__
