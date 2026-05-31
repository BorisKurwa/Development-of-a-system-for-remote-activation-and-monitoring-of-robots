import sys
import time
import threading
import os
import math
import pybullet as p
import pybullet_data
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer

class Go2AdvancedSimulation:
    def __init__(self):
        self.is_running = True
        
        p.connect(p.GUI)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        
        self.plane_id = p.loadURDF("plane.urdf")
        p.changeDynamics(self.plane_id, -1, lateralFriction=1.5, spinningFriction=1.0)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        go2_urdf_path = os.path.join(current_dir, "go2_description", "urdf", "go2_description.urdf")
        if not os.path.exists(go2_urdf_path):
            go2_urdf_path = os.path.join(current_dir, "go2_description", "urdf", "robot.urdf")

        self.go2_id = p.loadURDF(go2_urdf_path, [0.0, 0.0, 0.45], useFixedBase=False)
        
        self.joint_ids = []
        self.motor_names = []
        
        num_joints = p.getNumJoints(self.go2_id)
        for i in range(num_joints):
            joint_info = p.getJointInfo(self.go2_id, i)
            joint_name = joint_info[1].decode('utf-8')
            if 'hip' in joint_name or 'thigh' in joint_name or 'calf' in joint_name:
                self.joint_ids.append(i)
                self.motor_names.append(joint_name)
                p.setJointMotorControl2(self.go2_id, i, p.POSITION_CONTROL, targetPosition=0, force=80)

        self.walk_speed = 0.0
        self.turn_speed = 0.0
        self.phase = 0.0
        
        self.robot_state = "stand"
        
        self.jump_time = 0.0
        self.jump_phase = "none"
        
        self.target_base_hip = 0.0
        self.target_base_thigh = 0.85
        self.target_base_calf = -1.6
        
        self.current_base_hip = 0.0
        self.current_base_thigh = 0.85
        self.current_base_calf = -1.6

    def calculate_gait(self, phase, is_diagonal, name):
        if self.robot_state == "jump":
            return self.current_base_hip, self.current_base_thigh, self.current_base_calf

        if abs(self.walk_speed) < 0.05:
            return self.current_base_hip, self.current_base_thigh, self.current_base_calf
        
        if self.robot_state == "sit":
            return self.current_base_hip, self.current_base_thigh, self.current_base_calf
        
        p_phase = phase + math.pi if is_diagonal else phase
        
        swing = math.sin(p_phase)
        lift = max(0.0, math.cos(p_phase))
        
        thigh = self.current_base_thigh + (swing * 0.35 * self.walk_speed)
        calf = self.current_base_calf + (lift * 0.45) 
        
        return self.current_base_hip, thigh, calf

    def simulation_loop(self):
        while self.is_running:
            if p.getConnectionInfo()['isConnected'] == 0:
                break
            
            if self.robot_state == "jump":
                self.jump_time += 1./240.
                
                if self.jump_phase == "push":
                    self.current_base_hip = 0.0
                    self.current_base_thigh = -0.1
                    self.current_base_calf = -0.3
                    self.motor_force = 180.0
                    
                    if self.jump_time > 0.12:
                        self.jump_phase = "air"
                        
                elif self.jump_phase == "air":
                    self.current_base_hip = 0.0
                    self.current_base_thigh = 1.5
                    self.current_base_calf = -2.6
                    self.motor_force = 90.0
                    
                    if self.jump_time > 0.45:
                        self.jump_phase = "land"
                        
                elif self.jump_phase == "land":
                    self.target_base_thigh = 0.85
                    self.target_base_calf = -1.6
                    
                    self.current_base_thigh += (self.target_base_thigh - self.current_base_thigh) * 0.1
                    self.current_base_calf += (self.target_base_calf - self.current_base_calf) * 0.1
                    self.motor_force = 80.0
                    
                    if self.jump_time > 0.8:
                        self.robot_state = "stand"
                        self.jump_phase = "none"
            
            else:
                self.motor_force = 70.0
                if self.robot_state == "stand":
                    self.target_base_hip = 0.0
                    self.target_base_thigh = 0.85
                    self.target_base_calf = -1.6
                elif self.robot_state == "sit":
                    self.target_base_hip = 0.0
                    self.target_base_thigh = 1.45  
                    self.target_base_calf = -2.6   
                    
                self.current_base_hip += (self.target_base_hip - self.current_base_hip) * 0.05
                self.current_base_thigh += (self.target_base_thigh - self.current_base_thigh) * 0.05
                self.current_base_calf += (self.target_base_calf - self.current_base_calf) * 0.05

            if self.robot_state == "stand" and abs(self.walk_speed) > 0.01:
                self.phase += 0.15  
            else:
                self.phase = 0.0
            
            try:
                for i, name in zip(self.joint_ids, self.motor_names):
                    is_diagonal = ('FR' in name or 'RL' in name)
                    hip, thigh, calf = self.calculate_gait(self.phase, is_diagonal, name)
                    
                    if 'hip' in name:
                        target = hip
                    elif 'thigh' in name:
                        target = thigh
                    elif 'calf' in name:
                        target = calf
                        
                    p.setJointMotorControl2(self.go2_id, i, p.POSITION_CONTROL, targetPosition=target, force=self.motor_force)
                
                p.stepSimulation()
            except p.error:
                break
                
            time.sleep(1./240.)

    def set_move_direction(self, walk, turn):
        self.walk_speed = walk
        self.turn_speed = turn

    def set_robot_gait_state(self, state):
        if self.robot_state == "jump":
            return
        self.robot_state = state

    def trigger_jump(self):
        if self.robot_state == "stand" and self.jump_phase == "none":
            self.robot_state = "jump"
            self.jump_phase = "push"
            self.jump_time = 0.0

    def reset_robot_position(self):
        if p.getConnectionInfo()['isConnected'] == 0:
            return
        self.walk_speed = 0.0
        self.turn_speed = 0.0
        self.phase = 0.0
        self.robot_state = "stand"
        self.jump_phase = "none"
        
        pos, _ = p.getBasePositionAndOrientation(self.go2_id)
        safe_orientation = p.getQuaternionFromEuler([0, 0, 0])
        safe_position = [pos[0], pos[1], 0.45]
        
        p.resetBasePositionAndOrientation(self.go2_id, safe_position, safe_orientation)
        p.resetBaseVelocity(self.go2_id, linearVelocity=[0, 0, 0], angularVelocity=[0, 0, 0])
        
        self.current_base_hip = 0.0
        self.current_base_thigh = 0.85
        self.current_base_calf = -1.6
        
        for i, name in zip(self.joint_ids, self.motor_names):
            target = self.current_base_hip if 'hip' in name else (self.current_base_thigh if 'thigh' in name else self.current_base_calf)
            p.setJointMotorControl2(self.go2_id, i, p.POSITION_CONTROL, targetPosition=target, force=100)

    def stop(self):
        self.is_running = False
        time.sleep(0.1)
        if p.getConnectionInfo()['isConnected'] == 1:
            p.disconnect()


class Go2AdvancedController(QMainWindow):
    def __init__(self, sim_core):
        super().__init__()
        self.sim = sim_core
        self.setWindowTitle("Go2 Linear Controller")
        self.resize(320, 360)
        
        self.keys_pressed = {"forward": False, "backward": False}
        
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_movement_commands)
        self.ui_timer.start(30)
        
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Пульт управления Unitree Go2</b>", alignment=Qt.AlignmentFlag.AlignCenter))
        
        btn_forward = QPushButton("Вперед")
        btn_forward.pressed.connect(lambda: self.set_key_state("forward", True))
        btn_forward.released.connect(lambda: self.set_key_state("forward", False))
        
        btn_backward = QPushButton("Назад")
        btn_backward.pressed.connect(lambda: self.set_key_state("backward", True))
        btn_backward.released.connect(lambda: self.set_key_state("backward", False))
        
        layout.addWidget(btn_forward)
        layout.addWidget(btn_backward)
        
        layout.addWidget(QLabel("<b>Команды позы и трюков:</b>", alignment=Qt.AlignmentFlag.AlignLeft))
        
        btn_jump = QPushButton("ПРЫГНУТЬ")
        btn_jump.setStyleSheet("background-color: #20b2aa; color: white; font-weight: bold; font-size: 13px;")
        btn_jump.clicked.connect(self.sim.trigger_jump)
        layout.addWidget(btn_jump)
        
        hbox_pose = QHBoxLayout()
        btn_sit = QPushButton("ЛЕЧЬ")
        btn_sit.setStyleSheet("background-color: #f0ad4e; font-weight: bold;")
        btn_sit.clicked.connect(lambda: self.sim.set_robot_gait_state("sit"))
        
        btn_stand = QPushButton("ВСТАТЬ")
        btn_stand.setStyleSheet("background-color: #5cb85c; color: white; font-weight: bold;")
        btn_stand.clicked.connect(lambda: self.sim.set_robot_gait_state("stand"))
        hbox_pose.addWidget(btn_sit)
        hbox_pose.addWidget(btn_stand)
        layout.addLayout(hbox_pose)
        
        btn_reset = QPushButton("ВСТАТЬ НА НОГИ (RESET ПОЗИЦИИ)")
        btn_reset.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; margin-top: 10px;")
        btn_reset.clicked.connect(self.sim.reset_robot_position)
        layout.addWidget(btn_reset)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def set_key_state(self, key, is_pressed):
        if key in self.keys_pressed:
            self.keys_pressed[key] = is_pressed

    def update_movement_commands(self):
        walk = 0.0
        if self.keys_pressed["forward"]:
            walk = 1.0
        elif self.keys_pressed["backward"]:
            walk = -1.0
            
        self.sim.set_move_direction(walk, 0.0)

    def closeEvent(self, event):
        self.ui_timer.stop()
        self.sim.stop()
        event.accept()

if __name__ == '__main__':
    sim_core = Go2AdvancedSimulation()
    
    sim_thread = threading.Thread(target=sim_core.simulation_loop)
    sim_thread.daemon = True
    sim_thread.start()
    
    app = QApplication(sys.argv)
    window = Go2AdvancedController(sim_core)
    window.show()
    
    sys.exit(app.exec())