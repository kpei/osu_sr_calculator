from .Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from .Skills.Aim import Aim
from .Skills.Speed import Speed
from math import ceil, sqrt

class StarRatingCalculator(object):
    hitObjects = []
    difficultyMultiplier = 0.18
    displayDifficultyMultiplier = 0.605

    def calculate(self, hitObjects, timeRate):
        self.hitObjects = hitObjects
        aimSkill = Aim()
        speedSkill = Speed()

        for h in hitObjects:
            aimSkill.process(h)
            # speedSkill.process(h)

        aimRating = (aimSkill.difficultyValue() ** 0.75) * self.difficultyMultiplier
        speedRating = 0

        displayAimRating = (aimSkill.calculateDisplayDifficultyValue() ** 0.75) * self.displayDifficultyMultiplier
        displaySpeedRating = 0

        displayAimPerformance = (5.0 * max(1.0, displayAimRating) - 4.0) ** 3.0 / 100000.0
        displaySpeedPerformance = (5.0 * max(1.0, displaySpeedRating) - 4.0) ** 3.0 / 100000.0
        totalpp = (displayAimPerformance ** 1.1 + displaySpeedPerformance ** 1.1) ** (1.0/1.1)

        starRating = 0.027 * (((100000.0 / 2.0 ** (1.0 / 1.1) * totalpp) ** (1/3.0)) + 4.0)
        return {
            "aim": aimRating,
            "speed": speedRating,
            "total": starRating
        }