import logging

try:
    from .data_point import DataPoint
except ImportError:
    from classes.data_point import DataPoint

_LOGGER = logging.getLogger(__name__)


class SolarModule:
    def __init__(self, id, port, x,y):
        self.id = id
        self.port = port
        self.x = x
        self.y = y
        self.data_points = []  # List of DataPoint objects
    
    def add_data_point(self, data_point):
        self.data_points.append(data_point)

    def set_data(self, data, times):
        if len(data) != len(times):
            _LOGGER.warning("Data length %d does not match times length %d for module ID %s", len(data), len(times), self.id)
            return
        
        self.data_points = []  # Clear existing data points
        for time, value in zip(times, data):
            dp = DataPoint(time, value)
            self.add_data_point(dp)

    def getCurrentPower(self):
        if not self.data_points:
            return 0
        latest = self.data_points[-1]
        return latest.watt if latest.watt is not None else 0
        # _LOGGER.debug("Setting data for module %s: %s", self.id, self.data_points)

    def getLatestDataPoint(self):
        if not self.data_points:
            return None
        return self.data_points[-1]
    
    def getLatestTime(self):
        if not self.data_points:
            return None
        return self.data_points[-1].time

    def __repr__(self):
        return f"SolarModule(id={self.id}, port={self.port}, x={self.x}, y={self.y}, data_points={len(self.data_points)})" 