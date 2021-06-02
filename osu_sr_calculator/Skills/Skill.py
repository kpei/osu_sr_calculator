from ..Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from ..Objects.osu.HitObjects.Spinner import Spinner
from abc import ABC

class Skill(ABC):
    Previous = [] # array of DifficultyHitObject
    HistoryLength = 3

    def __init__(self):
        self.Previous = []
        self.HistoryLength = 3

    def addToHistory(self, currentObject):
        self.Previous.insert(0, currentObject)
        while(len(self.Previous) > self.HistoryLength):
            self.Previous.pop()