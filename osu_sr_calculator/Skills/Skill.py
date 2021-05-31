from ..Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from ..Objects.osu.HitObjects.Spinner import Spinner
from abc import ABC

class Skill(ABC):
    Previous = [] # array of DifficultyHitObject

    def __init__(self):
        self.Previous = []

    def addToHistory(self, currentObject):
        self.Previous.insert(0, currentObject)
        if(len(self.Previous) > 2):
            self.Previous.pop()