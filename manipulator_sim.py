import pybullet as p
import time
import pybullet_data

# 1. Подключаемся к графическому движку симуляции
physicsClient = p.connect(p.GUI)

# 2. Указываем путь к стандартным моделям, которые идут вместе с pybullet
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# 3. Устанавливаем гравитацию (чтобы робот "стоял" на земле, а предметы падали)
p.setGravity(0, 0, -9.81)

# 4. Загружаем плоскость (пол) и самого робота-манипулятора KUKA
planeId = p.loadURDF("plane.urdf")
# Робот загружается чуть выше пола, в координатах (0, 0, 0)
robotId = p.loadURDF("kuka_iiwa/model.urdf", [0, 0, 0], useFixedBase=True)

# 5. Получаем количество подвижных суставов (joints) робота
numJoints = p.getNumJoints(robotId)
print(f"Количество суставов робота: {numJoints}")

# 6. Создаем графические слайдеры (ползунки) в окне симуляции для управления
jointSliders = []
for i in range(numJoints):
    # Получаем информацию о каждом суставе (минимальный и максимальный угол поворота)
    jointInfo = p.getJointInfo(robotId, i)
    minPos = jointInfo[8]
    maxPos = jointInfo[9]
    
    # Если лимиты не заданы, ставим дефолтные от -пи до +пи градусов
    if minPos >= maxPos:
        minPos, maxPos = -3.14, 3.14
        
    # Создаем ползунок на панели GUI
    slider = p.addUserDebugParameter(f"Joint {i}", minPos, maxPos, 0.0)
    jointSliders.append(slider)

print("Симуляция запущена. Двигайте ползунки в правой части экрана!")

# 7. Основной цикл симуляции
try:
    while True:
        # Считываем значения с ползунков и отправляем команды роботу
        for i in range(numJoints):
            targetAngle = p.readUserDebugParameter(jointSliders[i])
            # Даем команду мотору занять целевой угол (позиционное управление)
            p.setJointMotorControl2(
                bodyUniqueId=robotId,
                jointIndex=i,
                controlMode=p.POSITION_CONTROL,
                targetPosition=targetAngle,
                force=500 # Сила мотора в Ньютонах
            )
        
        # Делаем один шаг расчета физики мира
        p.stepSimulation()
        time.sleep(1./240.) # Симуляция работает на частоте 240 Гц

except KeyboardInterrupt:
    # Корректный выход при закрытии терминала
    p.disconnect()