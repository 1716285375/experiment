import gymnasium as gym
from gymnasium import register
from envs.drone_env import AirSimDroneEnv

import random


register(
    id='AirSimDrone-v0',                          # 环境名字
    entry_point='__main__:AirSimDroneEnv',      # 创建环境的入口点
    # reward_threshold=np.inf,                    # 一个所能获得奖励的最大值
    # nondeterministic=True,                      # 环境是否是随机的
    # max_episode_steps=10,                       # 一个回合所能执行的最大步数
    # order_enforce=True,                         # 是否启用顺序执行器包装器以确保用户以正确的顺序运行函数
    # disable_env_checker=True,                   # 是否禁用 gymnasium.wrappers.PassiveEnvChecker
    # additional_wrappers=True,                   # 额外的包装器
    # vector_entry_point=True,                    # 用于创建矢量环境的入口点
    kwargs={
        'ip': '127.0.0.1',
        'image_shape': (144, 256, 1),
    }
)

if __name__ == '__main__':

    env = gym.make('AirSimDrone-v0')

    for episode in range(1000):
        env.reset()
        done = False
        while not done:
            a1 = random.randint(0, 2)
            a2 = random.randint(0, 2)
            action = [a1, a2]
            # print(action[0])
            # print(action[1])
            state, reward, terminated, truncated, info = env.step(action)
            print(state, action, reward, terminated, truncated, info)
            done = terminated or truncated
