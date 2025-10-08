try:
    from ..parsers import ProtobufParser
except ImportError:
    from parsers import ProtobufParser


class DataPoint:
    def __init__(self, time, value):
        self.time = time  # Expected to be a string in "HH:MM" format
        self.value = value  # Expected to be a float or int

        data = ProtobufParser.decode_data_point(value)

        self.volt = data[0] if len(data) > 0 else None
        self.ampere = data[1] if len(data) > 1 else None
        self.watt = data[2] if len(data) > 2 else None
        self.other = data[3:] if len(data) > 3 else []

        
    
    def __repr__(self):
        return f"DataPoint(time={self.time}, value={self.value}, volt={self.volt}, ampere={self.ampere}, watt={self.watt}, other={self.other})"