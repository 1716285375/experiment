import os
import time
import numpy as np
import json
import threading

import airsim
import gymnasium as gym
from gymnasium import spaces
from envs.airsim_env import AirSimEnv

from common.airsim_utils import *

from gymnasium import register

import random


class Drone:
    def __init__(self, ip='', counts=2):
        self.ip = ip
        self.counts = counts
        self.clients = []
        self.init()

    def init(self):
        for i in range(self.counts):
            client = airsim.MultirotorClient(ip=f"127.0.0.{i+1}")
            client.confirmConnection()
            self.clients.append(client)


class AirSimEnv(gym.Env):
    metadata = {"render.modes": ["rgb_array"]}

    def __init__(self, image_shape):
        self.s1 = gym.spaces.Box(-100.0, 100.0, shape=(1,))  # 队形期望误差

        self.space = [self.s1]
        self.observation_space = spaces.Tuple(self.space)
        self.viewer = None

    def __del__(self):
        raise NotImplementedError()

    def _get_obs(self):
        raise NotImplementedError()

    def _compute_reward(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def step(self, action):
        raise NotImplementedError()

    def render(self):
        return self._get_obs()


class AirSimDroneEnv(AirSimEnv):
    def __init__(self, ip, image_shape):
        super().__init__(image_shape)

        self.action_space = gym.spaces.Discrete(3)  # 动作空间

        self.ip_address = ip                                     # 调用者的ip地址
        self.airsim = Drone(ip=self.ip_address, counts=3)        # 无人机客户端
        self.drone_client = self.airsim.clients

        self.leader = self.drone_client[0]
        self.follower = self.drone_client[1]
        self.observer = self.drone_client[2]

        self.leader_callback_thread = threading.Thread(target=self.repeat_timer_leader_callback,
                                                       args=(self.leader_thread, 0.5))
        self.is_leader_thread_first_active = True
        self.is_leader_thread_first_end = True
        self.is_leader_thread_activa = False

        self.drone_name = ['UAV1', 'UAV2']
        self.current_step = 0
        self.episode = 10

    def repeat_timer_leader_callback(self, task, period):
        while self.is_leader_thread_activa:
            task()
            time.sleep(period)

    def start_leader_callback_thread(self):
        if not self.is_leader_thread_activa:
            self.is_leader_thread_activa = True
            if self.is_leader_thread_first_active:
                self.leader_callback_thread.start()
                self.is_leader_thread_first_active = False
            print("Started leader callback thread.")

    def stop_leader_callback_thread(self):
        if self.is_leader_thread_activa:
            self.is_leader_thread_activa = False
            # if self.is_leader_thread_first_end:
            #     self.leader_callback_thread.join()
            #     self.is_leader_thread_first_end = False
            print("Stopped leader callback thread.")

    def leader_thread(self):
        while True:
            if self.is_leader_thread_activa:
                self.leader.moveByVelocityZAsync(1, 0, -20, 1, vehicle_name=self.drone_name[0]).join()
            else:
                break
        pass

    def init(self):
        self.stop_leader_callback_thread()

        self.current_step = 0

        self.leader.reset()
        self.follower.reset()

        self.leader.enableApiControl(True, vehicle_name=self.drone_name[0])
        self.leader.armDisarm(True, vehicle_name=self.drone_name[0])

        self.follower.enableApiControl(True, vehicle_name=self.drone_name[1])
        self.follower.armDisarm(True, vehicle_name=self.drone_name[1])

        self.leader.moveToZAsync(-20, 5, vehicle_name=self.drone_name[0])  # 移动到指定的位置：（x, y, z），速度为2m/s
        self.follower.moveToZAsync(-20, 5, vehicle_name=self.drone_name[1]).join()  # 移动到指定的位置：（x, y, z），速度为2m/s

        self.start_leader_callback_thread()

    def _get_obs(self):
        s1 = np.zeros(1)
        state_current = [s1]
        state_leader = self.observer.getMultirotorState(vehicle_name=self.drone_name[0])
        state_follower = self.observer.getMultirotorState(vehicle_name=self.drone_name[1])
        print("leader: ", state_leader.kinematics_estimated.position.x_val)
        print("follower: ", state_follower.kinematics_estimated.position.x_val)
        return state_current
        pass

    def _do_action(self, action):
        self.follower.moveByVelocityZAsync(action, 0, -20, 1, vehicle_name=self.drone_name[1]).join()

    def step(self, action):
        self.current_step += 1
        obs = self._get_obs()
        self._do_action(action)
        reward = 1
        terminated = False
        if self.current_step >= self.episode:
            truncated = True
        else:
            truncated = False

        info = {}

        return obs, reward, terminated, truncated, info

    def reset(self):
        self.init()
        return self._get_obs()
        pass

    def close(self):
        pass

    def render(self):
        pass


if __name__ == '__main__':
    register(
        id='AirSimDrone-v0',
        entry_point='__main__:AirSimDroneEnv',
        kwargs={
            'ip': '127.0.0.1',
            'image_shape': (144, 256, 1),
            # "render_modes": "rgb_array",
        }
    )

    env = gym.make('AirSimDrone-v0')
    for episode in range(10):
        time.sleep(0.5)
        env.reset()
        done = False

        while not done:
            action = random.randint(0, 2)

            state, reward, terminated, truncated, info = env.step(action)
            time.sleep(1)
            print(state, action, reward, terminated, truncated, info)
            done = terminated or truncated

        print('Episode:', episode, 'Done', done)