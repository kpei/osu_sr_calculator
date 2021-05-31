from ..Objects.osu.HitObjects.Spinner import Spinner
from ..Objects.osu.HitObjects.HitObject import HitObject
from ..Objects.Vector2 import Vector2
from ..Skills.OsuSkill import OsuSkill
from ..Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from math import log, pi, sqrt, sin
from copy import deepcopy

class Aim(OsuSkill):
    STARS_PER_DOUBLE = 1.1
    HISTORY_LENGTH = 2
    DECAY_EXCESS_THRESHOLD = 500
    BASE_DECAY = 0.75

    DISTANCE_CONSTANT = 3.5
    SNAP_STRAIN_MULTIPLIER = 23.727
    FLOW_STRAIN_MULTIPLIER = 30.727
    SLIDER_STRAIN_MULTIPLIER = 75
    TOTAL_STRAIN_MULTIPLIER = .1675

    currStrain = 1
    
    def flowStrainOf(self, previousObject: DifficultyHitObject, currentObject: DifficultyHitObject, nextObject: DifficultyHitObject, 
        prevVector: Vector2, currVector: Vector2, nextVector: Vector2):
        observedDistance: Vector2 = currVector.subtract(prevVector.scale(0.1))

        prevAngularMomentumChange = abs(currentObject.Angle * currVector.length() - previousObject.Angle * prevVector.length())
        nextAngularMomentumChange = abs(currentObject.Angle * currVector.length() - nextObject.Angle * nextVector.length())

        angularMomentumChange = sqrt( min(currVector.length(), prevVector.length()) * abs(nextAngularMomentumChange - prevAngularMomentumChange) / (2 * pi) )
        # buff for changes in angular momentum, but only if the momentum change doesnt equal the previous.

        momentumChange = sqrt( max(0, prevVector.length() - currVector.length()) * min(currVector.length(), prevVector.length()) )
        # reward for accelerative changes in momentum

        strain = currentObject.FlowProbability * \
            ( observedDistance.length() + max( momentumChange * (0.5 + 0.5 * previousObject.FlowProbability), angularMomentumChange * previousObject.FlowProbability ) )

        strain *= min( currentObject.StrainTime / (currentObject.StrainTime - 10.0), previousObject.StrainTime / (previousObject.StrainTime - 10.0) )
        # buff high BPM slightly.

        return strain

    # mans using fitt's Law in a circle game sheeeeesh
    def snapScaling(self, distance):
        distanceDiff: float = distance - self.DISTANCE_CONSTANT
        return 1.0 if (distanceDiff < 0) else ( (self.DISTANCE_CONSTANT + distanceDiff * (log(1 + distanceDiff / sqrt(2)) / log(2)) / distanceDiff) / distance )

    def snapStrainOf(self, previousObject: DifficultyHitObject, currentObject: DifficultyHitObject, nextObject: DifficultyHitObject, 
        prevVector: Vector2, currVector: Vector2, nextVector: Vector2):
        currVector = currVector.scale(self.snapScaling(currentObject.JumpDistance / 100.0))
        prevVector = prevVector.scale(self.snapScaling(previousObject.JumpDistance / 100.0))

        observedDistance = currVector.add(prevVector.scale(0.35))

        strain = observedDistance.length() * currentObject.SnapProbability
        strain *= min( currentObject.StrainTime / (currentObject.StrainTime - 20.0), previousObject.StrainTime / (previousObject.StrainTime - 20.0) )

        return strain

    def sliderStrainOf(self, previousObject: DifficultyHitObject, currentObject: DifficultyHitObject, nextObject: DifficultyHitObject):
        return previousObject.TravelDistance / previousObject.StrainTime

    def strainValueOf(self, currentObject: DifficultyHitObject):
        if(isinstance(currentObject, Spinner)):
            return 0
        
        osuCurrent = deepcopy(currentObject)
        strain = 0
        if(len(self.Previous) > 1):
            osuNextObject = currentObject
            osuCurrObject: DifficultyHitObject = self.Previous[0]
            osuPrevObject: DifficultyHitObject = self.Previous[1]
            # Since it is easier to get history, we take the previous[0] as our current, so we can see our "next"

            nextVector = osuNextObject.DistanceVector.divide(osuNextObject.StrainTime)
            currVector = osuCurrObject.DistanceVector.divide(osuCurrObject.StrainTime)
            prevVector = osuPrevObject.DistanceVector.divide(osuPrevObject.StrainTime)

            snapStrain = self.snapStrainOf(osuPrevObject, osuCurrObject, osuNextObject, prevVector, currVector, nextVector)
            flowStrain = self.flowStrainOf(osuPrevObject, osuCurrObject, osuNextObject, prevVector, currVector, nextVector)
            sliderStrain = self.sliderStrainOf(osuPrevObject, osuCurrObject, osuNextObject)

            self.currStrain *= self.computeDecay(self.BASE_DECAY, osuCurrent.StrainTime)
            self.currStrain += snapStrain * self.SNAP_STRAIN_MULTIPLIER
            self.currStrain += flowStrain * self.FLOW_STRAIN_MULTIPLIER
            self.currStrain += sliderStrain * self.SLIDER_STRAIN_MULTIPLIER

            strain = self.TOTAL_STRAIN_MULTIPLIER * self.currStrain
        
        return strain