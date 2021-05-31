from math import e, log, log2
from ..Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from ..Objects.osu.HitObjects.Spinner import Spinner
from .Skill import Skill

class OsuSkill(Skill):

    strains = []
    times = []

    TARGET_FC_PRECISION = 0.01
    DECAY_EXCESS_THRESHOLD = 500
    BASE_DECAY = 0.75
    STARS_PER_DOUBLE = 1.1
    
    DIFFICULTY_EXPONENT = 1.0 / log2(STARS_PER_DOUBLE)

    totalLength = lambda self: self.times[-1] - self.times[0]
    targetFCTime = 30 * 60 * 1000 # estimated time it takes us to FC (30 minutes) 

    def strainValueOf(self, currentObject):
        pass

    def computeDecay(self, baseDecay, deltaTime):
        # Beyond 500 MS (or whatever DECAY_EXCESS_THRESHOLD is), we decay geometrically to avoid keeping strain going over long breaks.
        decay = baseDecay if (deltaTime < self.DECAY_EXCESS_THRESHOLD) else ( baseDecay ** (1000.0 / min(deltaTime, self.DECAY_EXCESS_THRESHOLD)) ) ** (deltaTime / 1000.0)
        return decay

    def process(self, currentObject):
        self.strains.append(self.strainValueOf(currentObject))
        self.times.append(currentObject.StartTime)
        self.addToHistory(currentObject)

    def calculateDifficultyValue(self):
        print(self.strains)
        SR = sum(map(lambda s: s ** self.DIFFICULTY_EXPONENT, self.strains))
        return SR ** (1.0 / self.DIFFICULTY_EXPONENT)

    def calculateDisplayDifficultyValue(self):
        self.strains.sort(reverse=True)

        difficulty = 0
        weight = 1

        for strain in self.strains:
            difficulty += strain * weight
            weight *= 0.9

        return difficulty

    def difficultyValue(self):
        return self.fcTimeSkillLevel(self.calculateDifficultyValue())

    # renamed to skillLevel due to ambiguity - infact all these namings are bad :o

    def fcProbability(self, skillLevel, difficulty):
        return e ** (-1.0 * (difficulty / max(1e-10, skillLevel)) ** (self.DIFFICULTY_EXPONENT))

    def skillLevel(self, probability, difficulty):
        return difficulty * ( -1.0 * log(probability) ) ** ( -1 / self.DIFFICULTY_EXPONENT )

    def expectedTargetTime(self, totalDifficulty):
        targetTime = 0
        for i in range(1,len(self.times)):
            targetTime += min(2000, self.times[i] - self.times[i-1]) * (self.strains[i] / totalDifficulty)
        return targetTime
    
    def expectedFCTime(self, skillLevel):
        lastTimestamp = self.times[0] - 5
        fcTime = 0

        for i, strain in enumerate(self.strains):
            deltaTime = self.times[i] - lastTimestamp
            lastTimestamp = self.times[i]
            fcTime = (fcTime + deltaTime) / self.fcProbability(skillLevel, strain)

        return fcTime - self.totalLength()

    def fcTimeSkillLevel(self, totalDifficulty):
        lengthEstimate = 0.4 * self.totalLength()
        print(totalDifficulty)
        self.targetFCTime += 45 * max(0, self.expectedTargetTime(totalDifficulty) - 60000)
        # for every minute of straining time past 1 minute, add 45 mins to estimated time to FC.
        fcProb = lengthEstimate / self.targetFCTime
        skillLevel = self.skillLevel(fcProb, totalDifficulty)

        for _ in range(5):
            fcTime = self.expectedFCTime(skillLevel)
            lengthEstimate = fcTime * fcProb
            skillLevel = self.skillLevel(fcProb, totalDifficulty)
            # Convergence check
            if( abs(fcTime - self.targetFCTime) < self.TARGET_FC_PRECISION * self.targetFCTime ):
                break

        return skillLevel