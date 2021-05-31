from .HitObject import HitObject

class DifficultyHitObject(HitObject):
    TravelDistance = None
    JumpDistance = None
    Angle = None
    DeltaTime = None
    StrainTime = None

    CurrentObject = None
    LastObject = None
    LastLastObject = None

    FlowProbability = 0
    SnapProbability = 1.0 - FlowProbability
    DistanceVector = None

    def __init__(self, currentObject, lastObject, lastLastObject, travelDistance, jumpDistance, angle, flowProbability, distanceVector, deltaTime, strainTime):
        super().__init__(currentObject.Position, currentObject.StartTime, radius=currentObject.Radius)
        self.TravelDistance = travelDistance
        self.JumpDistance = jumpDistance
        self.FlowProbability = flowProbability
        self.SnapProbability = 1.0 - self.FlowProbability
        self.DistanceVector = distanceVector
        self.Angle = angle
        self.DeltaTime = deltaTime
        self.StrainTime = strainTime

        self.CurrentObject = currentObject
        self.LastObject = lastObject
        self.LastLastObject = lastLastObject