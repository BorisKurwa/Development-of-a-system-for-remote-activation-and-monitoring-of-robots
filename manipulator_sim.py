import pybullet as p
import time
import pybullet_data

physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.81)

planeId = p.loadURDF("plane.urdf")
robotId = p.loadURDF("kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True)

numJoints = p.getNumJoints(robotId)
print(f"Количество суставов робота: {numJoints}")

jointSliders = []
for i in range(numJoints):
    jointInfo = p.getJointInfo(robotId, i)
    minPos = jointInfo[8]
    maxPos = jointInfo[9]
    
    if minPos >= maxPos:
        minPos, maxPos = -3.14, 3.14
        
    slider = p.addUserDebugParameter(f"Joint {i}", minPos, maxPos, 0.0)
    jointSliders.append(slider)

print("Симуляция запущена. Двигайте ползунки в правой части экрана!")

try:
    while True:
        for i in range(numJoints):
            targetAngle = p.readUserDebugParameter(jointSliders[i])
            p.setJointMotorControl2(
                bodyUniqueId=robotId,
                jointIndex=i,
                controlMode=p.POSITION_CONTROL,
                targetPosition=targetAngle,
                force=500
            )
        
        p.stepSimulation()
        time.sleep(1./240.)

except KeyboardInterrupt:
    p.disconnect()