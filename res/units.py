from enum import Enum


class Units(Enum):
    PRESSURE = "Druck", "bar"
    CONDUCTIVITY = "Leitfähigkeit", "S/m"
    TEMPERATURE = "Temperatur", "°C"
    LEVEL = "Füllstand", "l"
    PH = "ph-Wert", ""
    ANGLE = "Winkel", "°"
    STATE = "Zustand", ""

    def choice(self):
        return self.name, f"{self.value[0]} [{self.value[1]}]"
