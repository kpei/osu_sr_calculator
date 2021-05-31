from copy import deepcopy
from ..Objects.osu.HitObjects.Spinner import Spinner
from .OsuSkill import OsuSkill
from ..Objects.osu.HitObjects.Slider import Slider
from ..Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from math import log2, sqrt

class Tap(OsuSkill):
    def __init__(self):
        super().__init__()

        self.STARS_PER_DOUBLE = 1.075
        self.HISTORY_LENGTH = 16
        self.DECAY_EXCESS_THRESHOLD = 500
        self.BASE_DECAY = 0.9

        self.STRAIN_TIME_BUFF_RANGE = 75
        self.SINGLE_MULTIPLIER = 2.375
        self.STRAIN_MULTIPLIER = 2.725
        self.RHYTHM_MULTIPLIER = 1
        
        self.currStrain = 1
        self.singleStrain = 1
        self.DIFFICULTY_EXPONENT = 1.0 / log2(self.STARS_PER_DOUBLE)

    def isRatioEqual(self, ratio, a, b):
        return (a + 15 > ratio * b) and (a - 15 < ratio * b)

    def calculateRhythmDifficulty(self):
        islandSizes = [0.0]*7
        islandTimes = [0.0]*7
        islandSize = 0
        specialTransitionCount = 0.0
        firstDeltaSwitch = False

        for i in range(1, len(self.Previous)):
            prevDelta = self.Previous[i - 1].StrainTime
            currDelta = self.Previous[i].StrainTime

            # idk just a guess at the name
            cumulativeTimePerHistory = (float(i) / self.HISTORY_LENGTH) / sqrt(prevDelta * currDelta)

            if (self.isRatioEqual(1.5, prevDelta, currDelta) or self.isRatioEqual(1.5, currDelta, prevDelta)):
                if(isinstance(self.Previous[i - 1], Slider) or isinstance(self.Previous[i], Slider)):
                    specialTransitionCount += 50.0 * cumulativeTimePerHistory
                else:
                    specialTransitionCount += 250.0 * cumulativeTimePerHistory

            if(firstDeltaSwitch):
                if(self.isRatioEqual(1.0, prevDelta, currDelta)):
                    islandSize += 1 # island is still progressing, count size.
                elif (prevDelta > currDelta * 1.25): # we're speeding up
                    if (islandSize > 6):
                        islandTimes[6] = islandTimes[6] + 100.0 * cumulativeTimePerHistory
                        islandSizes[6] += 1
                    else:
                        islandTimes[islandSize] = islandTimes[islandSize] + 100.0 * cumulativeTimePerHistory
                        islandSizes[islandSize] += 1
                    
                    islandSize = 0 # reset and count again, we sped up (usually this could only be if we did a 1/2 -> 1/3 -> 1/4) (or 1/1 -> 1/2 -> 1/4)
                else: # we're not the same or speeding up, must be slowing down.
                    if (islandSize > 6):
                        islandTimes[6] = islandTimes[6] + 100.0 * cumulativeTimePerHistory
                        islandSizes[6] += 1
                    else:
                        islandTimes[islandSize] = islandTimes[islandSize] + 100.0 * cumulativeTimePerHistory
                        islandSizes[islandSize] += 1

                    firstDeltaSwitch = False # stop counting island until next speed up.
            elif (prevDelta > 1.25 * currDelta): # we want to be speeding up
                # Begin counting island until we slow again.
                firstDeltaSwitch = True
                islandSize = 0

        rhythmComplexitySum = 0.0
        for (size, time) in zip(islandSizes, islandTimes):
            rhythmComplexitySum += time / size ** 0.5 if size != 0 else 0 # sum the total amount of rhythm variance, penalizing for repeated island sizes.
        rhythmComplexitySum += specialTransitionCount

        return sqrt(4.0 + rhythmComplexitySum * self.RHYTHM_MULTIPLIER) / 2

    def strainValueOf(self, currentObject: DifficultyHitObject):
        if (currentObject is Spinner or len(self.Previous) == 0):
            return 0
        
        osuCurrent = currentObject

        avgDeltaTime = (osuCurrent.StrainTime + max(50, self.Previous[0].DeltaTime)) / 2.0

        rhythmComplexity = self.calculateRhythmDifficulty()

        # scale tap value for high BPM (above 200).
        strainValue = 0.25 + (self.STRAIN_TIME_BUFF_RANGE / avgDeltaTime) ** (2 if (self.STRAIN_TIME_BUFF_RANGE / avgDeltaTime > 1) else 1)

        self.singleStrain *= self.computeDecay(self.BASE_DECAY, osuCurrent.StrainTime)
        self.singleStrain += (0.5 + osuCurrent.SnapProbability) * strainValue * self.SINGLE_MULTIPLIER

        self.currStrain *= self.computeDecay(self.BASE_DECAY, osuCurrent.StrainTime)
        self.currStrain += strainValue * self.STRAIN_MULTIPLIER

        return max( min( (1 / (1 - self.BASE_DECAY)) * strainValue * self.STRAIN_MULTIPLIER, self.currStrain * rhythmComplexity), # prevent over buffing strain past death stream level
            self.singleStrain) # we use a seperate strain for singles to not complete nuke boring 1-2 maps