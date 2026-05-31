# Управление роботами: KUKA iiwa & Unitree Go2

Учебный проект по дисциплине **«Прикладные интеллектуальные системы»**  
Брестский государственный технический университет, кафедра ИИТ  
Группа ИИ-25 — Андреюк М. О., Жук Б. Д.

---

## О проекте

Проект охватывает два направления:

- **Симуляция манипулятора KUKA iiwa** в физическом движке PyBullet
- **ROS-пакет для четвероногого робота Unitree Go2** — URDF-описание, симуляция в Gazebo и RViz

Управление реализуется через Ethernet-подключение с использованием **Unitree SDK2** и протокола **DDS (Data Distribution Service)**.

---

## Структура лабораторных работ

| № | Тема | Содержание |
|---|------|-----------|
| Лаб. 1 | План проекта | Постановка целей, разбивка на этапы |
| Лаб. 2 | Анализ аппаратной части | Характеристики Go2, DOF, FSM-состояния |
| Лаб. 3 | Настройка системы управления | WSL2, SDK2, CycloneDDS, сеть |
| Лаб. 4 | Реализация режимов работы | API управления: движение, жесты, FSM |

---

## Структура проекта

```
project/
├── manipulator_sim.py              # Симуляция манипулятора KUKA iiwa (PyBullet)
└── go2_simulation/
    ├── simulation_app.py           # Альтернативный запуск симуляции KUKA
    └── go2_description/            # ROS-пакет: URDF-описание робота Go2
        ├── config/
        │   ├── robot_control.yaml  # PID-параметры контроллеров суставов
        │   └── joint_names_go2_description.yaml
        ├── launch/
        │   ├── gazebo.launch       # Запуск в Gazebo
        │   └── go2_rviz.launch     # Визуализация в RViz
        ├── urdf/
        │   └── go2_description.urdf
        ├── xacro/                  # Xacro-шаблоны модели
        └── meshes/                 # 3D-меши (.dae): база, бедро, голень, стопа
```

---

## Компоненты

### 1. Симуляция манипулятора KUKA iiwa (PyBullet)

Интерактивная симуляция 7-степенного манипулятора с управлением через GUI-слайдеры.

**Возможности:**
- Физическая симуляция с гравитацией (9.81 м/с²)
- GUI-слайдеры для управления каждым суставом в реальном времени
- Позиционное управление моторами (500 Н)
- Частота симуляции: **240 Гц**
- Автоматическое определение лимитов суставов из URDF

#### Требования

```bash
pip install pybullet
```

#### Запуск

```bash
python manipulator_sim.py
```

---

### 2. ROS-пакет `go2_description` (Unitree Go2)

URDF/Xacro описание четвероногого робота **Unitree Go2** для использования в Gazebo, RViz и других симуляторах (Isaac Gym и др.).

**Суставы (12 DoF):**

| Нога | Hip | Thigh | Calf |
|------|-----|-------|------|
| FL (передняя левая) | FL_hip_joint | FL_thigh_joint | FL_calf_joint |
| FR (передняя правая) | FR_hip_joint | FR_thigh_joint | FR_calf_joint |
| RL (задняя левая) | RL_hip_joint | RL_thigh_joint | RL_calf_joint |
| RR (задняя правая) | RR_hip_joint | RR_thigh_joint | RR_calf_joint |

**PID-параметры контроллеров:**

| Сустав | P | I | D |
|--------|---|---|---|
| Hip | 100.0 | 0.0 | 5.0 |
| Thigh | 300.0 | 0.0 | 8.0 |
| Calf | 300.0 | 0.0 | 8.0 |

#### Требования

- ROS (Noetic / Melodic)
- `catkin`, `robot_state_publisher`, `joint_state_publisher_gui`
- `gazebo_ros`, `unitree_legged_control`

#### Сборка

```bash
mkdir -p ~/catkin_ws/src && cd ~/catkin_ws/
catkin init
cd src && git clone <repo_url>
catkin build
source ~/catkin_ws/devel/setup.bash
```

#### Запуск

```bash
# Визуализация в RViz
roslaunch go2_description go2_rviz.launch

# Симуляция в Gazebo
roslaunch go2_description gazebo.launch
```

---

## Архитектура управления (FSM)

Робот использует **конечный автомат (FSM)** для переключения между режимами:

| FSM ID | Состояние | Описание |
|--------|-----------|----------|
| 0 | Zero Torque | Отключение момента на моторах |
| 1 | Damp | Режим демпфирования (безопасное состояние) |
| 2 | Squat | Положение приседа |
| 3 | Sit | Положение сидя |
| 4 | Stand | Положение стоя, готовность к ходьбе |
| 500 | Start | Начальная инициализация |

---

## Настройка окружения

### 1. WSL2 + Ubuntu 22.04

```powershell
# PowerShell (Администратор)
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
wsl --set-default-version 2
# Затем установить Ubuntu 22.04 LTS из Microsoft Store
```

### 2. Инструменты разработки в Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git python3-venv cmake
```

### 3. Сетевое подключение

Статический IP на Windows:

```
IP-адрес:  192.168.123.222
Маска:     255.255.255.0
```

Проверка связи с роботом:

```bash
ping 192.168.123.164
```

### 4. Unitree SDK2

```bash
mkdir -p ~/go2_project && cd ~/go2_project
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
pip install -e .
```

### 5. CycloneDDS

```bash
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install

export CYCLONEDDS_HOME="$HOME/cyclonedds/install"
```

---

## Настройка модели столкновений (для Isaac Gym)

В файле `go2_description/urdf/go2_description.urdf` для линков `FL_thigh`, `FR_thigh`, `RL_thigh`, `RR_thigh`:

```xml
<!-- По умолчанию -->
<box size="0.213 0.0245 0.034" />

<!-- Укороченная модель для обучения (избегает пересечений thigh/calf) -->
<box size="0.11 0.0245 0.034" />
```

| Модель | Превью |
|--------|--------|
| Стандартная | `urdf/Normal_collision_model.png` |
| Изменённая | `urdf/Amended_collision_model.png` |
