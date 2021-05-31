from .Objects.osu.HitObjects.HitObject import HitObject
from .Objects.osu.HitObjects.DifficultyHitObject import DifficultyHitObject
from .Objects.osu.HitObjects.Slider import Slider
from .Objects.osu.HitObjects.Spinner import Spinner
from .Objects.Vector2 import Vector2
from math import atan2, e, pi, sin

class DifficultyHitObjectCreator(object):
    difficultyHitObjects = []

    lastLastObject = None
    lastObject = None
    currentObject = None
    timeRate = None

    normalized_radius = 50
    TravelDistance = 0
    JumpDistance = 0
    Angle = 0
    DeltaTime = 0
    StrainTime = 0

    FlowProbability = 0
    DistanceVector = Vector2(0.0, 0.0)

    def clamp(self, value, _min, _max):
        return max(min(value, _max), _min)

    def convertToDifficultyHitObjects(self, hitObjects, timeRate):
        self.difficultyHitObjects = []

        for i in range(1, len(hitObjects)):
            lastLast = hitObjects[i - 2] if i > 1 else None
            last = hitObjects[i - 1]
            current = hitObjects[i]

            difficultyHitObject = self.createDifficultyHitObject(lastLast, last, current, timeRate)
            self.difficultyHitObjects.append(difficultyHitObject)

        return self.difficultyHitObjects

    def createDifficultyHitObject(self, lastLast, last, current, timeRate):
        self.lastLastObject = lastLast
        self.lastObject = last
        self.currentObject = current
        self.timeRate = timeRate

        self.setDistances()
        self.setTimingValues()
        self.calculateFlowProbability()

        return DifficultyHitObject(self.currentObject, self.lastObject, self.lastLastObject, self.TravelDistance, self.JumpDistance, self.Angle, self.FlowProbability, self.DistanceVector, self.DeltaTime, self.StrainTime)

    def setDistances(self):
        self.TravelDistance = 0
        self.JumpDistance = 0
        self.Angle = 0
        self.DeltaTime = 0
        self.StrainTime = 0

        # so sometimes spinners have no Radius property set??? 
        if(self.currentObject.Radius is None):
            self.currentObject.Radius = self.normalized_radius

        scalingFactor = self.normalized_radius / self.currentObject.Radius
        if(self.currentObject.Radius < 32):
            smallCircleBonus = min(32 - self.currentObject.Radius, 5) / 50
            scalingFactor *= 1 + smallCircleBonus
        
        if(isinstance(self.lastObject, Slider)):
            lastSlider = self.lastObject
            self.computeSliderCursorPosition(lastSlider)
            self.TravelDistance = lastSlider.LazyTravelDistance * scalingFactor

        lastCursorPosition = self.getEndCursorPosition(self.lastObject)

        if(not isinstance(self.currentObject, Spinner)):
            self.DistanceVector = self.currentObject.StackedPosition.scale(scalingFactor).subtract(lastCursorPosition.scale(scalingFactor))
            self.JumpDistance = self.DistanceVector.length()
        
        if(self.lastLastObject is not None):
            lastLastCursorPosition = self.getEndCursorPosition(self.lastLastObject)

            v1 = lastLastCursorPosition.subtract(self.lastObject.StackedPosition)
            v2 = self.currentObject.StackedPosition.subtract(lastCursorPosition)

            dot = v1.dot(v2)
            det = v1.x * v2.y - v1.y * v2.x

            self.Angle = abs(atan2(det, dot))
            self.Angle = 0 if(self.Angle == None) else self.Angle

    def setTimingValues(self):
        self.DeltaTime = (self.currentObject.StartTime - self.lastObject.StartTime) / self.timeRate
        self.StrainTime = max(50, self.DeltaTime)

    def computeSliderCursorPosition(self, slider):
        if(slider.LazyEndPosition is not None):
            return
        slider.LazyEndPosition = slider.StackedPosition
        slider.LazyTravelDistance = 0

        approxFollowCircleRadius = slider.Radius * 3
        def computeVertex(t):
            progress = (t - slider.StartTime) / slider.SpanDuration
            if(progress % 2 >= 1):
                progress = 1 - progress % 1
            else:
                progress = progress % 1
            
            diff = slider.StackedPosition.add(slider.Path.PositionAt(progress)).subtract(slider.LazyEndPosition)
            dist = diff.length()

            if(dist > approxFollowCircleRadius):
                diff.normalize()
                dist -= approxFollowCircleRadius
                slider.LazyEndPosition = slider.LazyEndPosition.add(diff.scale(dist))
                slider.LazyTravelDistance = dist if slider.LazyTravelDistance is None else slider.LazyTravelDistance + dist

        def mapFunc(t):
            return t.StartTime
        scoringTimes = map(mapFunc, slider.NestedHitObjects[1:len(slider.NestedHitObjects)])

        for time in scoringTimes:
            computeVertex(time)

    def getEndCursorPosition(self, obj):
        pos = obj.StackedPosition

        if(isinstance(obj, Slider)):
            self.computeSliderCursorPosition(obj)
            pos = obj.LazyEndPosition if obj.LazyEndPosition is not None else pos

        return pos
    
    def calculateFlowProbability(self):
        deltaTime = self.DeltaTime
        distance = self.JumpDistance
        angle = self.Angle

        angle = self.clamp(angle, pi / 6, pi / 2)
        angleOffset = 10.0 * sin(1.5 * (pi / 2 - angle))
        distanceOffset = distance ** 1.7 / 325

        flow = self.clamp((deltaTime - 126.0 + distanceOffset + angleOffset), -1e2, 1e2)
        self.FlowProbability = 1.0 / (1.0 + e ** flow)