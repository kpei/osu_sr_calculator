from ..Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from ..Objects.osu.HitObjects.Spinner import Spinner
from abc import ABC

class Skill(ABC):
    Previous = [] # array of DifficultyHitObject

    def __init__(self):
        self.Previous = []

    def process(self, currentObject):
        pass

    def difficultyValue(self):
        self.strainPeaks.sort(reverse=True)

        difficulty = 0
        weight = 1

        for strain in self.strainPeaks:
            difficulty += strain * weight
            weight *= 0.9

        return difficulty

    def strainValueOf(self, currentObject):
        pass

    def strainDecay(self, ms):
        return pow(self.StrainDecayBase, ms / 1000)

    def addToHistory(self, currentObject):
        self.Previous.insert(0, currentObject)
        if(len(self.Previous) > 2):
            self.Previous.pop()