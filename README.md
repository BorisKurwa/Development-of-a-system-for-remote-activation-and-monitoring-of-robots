# Управление роботом-гуманоидом Unitree G1

Учебный проект по дисциплине **«Прикладные интеллектуальные системы»**  
Брестский государственный технический университет, кафедра ИИТ  
Группа ИИ-25 — Андреюк М. О., Жук Б. Д.

---

## О проекте

Система удалённого управления роботом-гуманоидом **Unitree G1** с компьютера на базе Windows через Ethernet-подключение с использованием официального **Unitree SDK2** и протокола **DDS (Data Distribution Service)**.

---

## Структура лабораторных работ

| № | Тема | Содержание |
|---|------|-----------|
| Лаб. 1 | План проекта | Постановка целей, разбивка на этапы |
| Лаб. 2 | Анализ аппаратной части | Характеристики G1, DOF, FSM-состояния |
| Лаб. 3 | Настройка системы управления | WSL2, SDK2, CycloneDDS, сеть |
| Лаб. 4 | Реализация режимов работы | API управления: движение, жесты, FSM |

---

## Технические характеристики Unitree G1

| Параметр | Значение |
|----------|----------|
| Высота (стоя) | 1320 мм (в сложенном — 690 мм) |
| Вес | ~35 кг (с батареей) |
| Степени свободы (DOF) | 23–43 (зависит от комплектации) |
| Скорость движения | до 2 м/с (спринт до 3.3 м/с) |
| Макс. крутящий момент | 90–120 Н·м |
| Время работы | ~2 часа (батарея 9000 мАч) |

**Распределение DOF:**

| Часть тела | DOF |
|-----------|-----|
| Ноги (каждая) | 6 (бедро ×3, колено ×1, голеностоп ×2) |
| Руки (каждая) | 5 (плечо, локоть, запястье) |
| Поясница | 1–3 (зависит от версии) |
| Кисти (опционально) | до 7 (Dex3-1) |

---

## Архитектура управления

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

Подключение по Ethernet, статический IP на Windows:

```
IP-адрес:    192.168.123.222
Маска:       255.255.255.0
```

Проверка связи с роботом:

```bash
ping 192.168.123.164
```

### 4. Unitree SDK2

```bash
mkdir -p ~/g1_robot_project && cd ~/g1_robot_project
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

## API управления роботом

### Команды движения (`Move`)

| Параметр | Диапазон | Описание |
|----------|----------|----------|
| `vx` | -0.5 ... 0.5 м/с | Скорость вперёд/назад |
| `vy` | -0.3 ... 0.3 м/с | Скорость вбок |
| `vyaw` | -1.0 ... 1.0 рад/с | Угловая скорость поворота |
| `continuous` | bool | `True` — движение до `StopMove()` |

### Основные методы

| Метод | FSM / API | Назначение |
|-------|-----------|-----------|
| `Squat2StandUp()` | FSM 4 | Встать из приседа |
| `StandUp2Squat()` | FSM 2 | Присесть из стоя |
| `Damp()` | FSM 1 | Режим демпфирования |
| `ZeroTorque()` | FSM 0 | Отключение момента |
| `Move(vx, vy, vyaw, continuous)` | API 7105 | Движение |
| `StopMove()` | API 7105 | Остановка |
| `WaveHand(turn_flag)` | Task 0/1 | Жест «помахать» |
| `ShakeHand(stage)` | Task 2/3 | Жест «пожать руку» |
| `HighStand()` / `LowStand()` | API 7104 | Изменение высоты корпуса |
