"""
Script for benchmarking PPO Agent
"""

import time
from mushroom_rl_benchmark import BenchmarkExperiment, BenchmarkLogger
from mushroom_rl_benchmark.builders import EnvironmentBuilder, PPOBuilder

if __name__ == '__main__':

    logger = BenchmarkLogger(
        log_dir='./logs', 
        log_id='ppo_pendulum'
    )

    agent_builder = PPOBuilder.default(
        actor_lr=3e-4,
        critic_lr=3e-4,
        n_features=32
    )

    env_name = 'Gym'
    env_params = dict(
        env_id='Pendulum-v0', 
        horizon=200, 
        gamma=.99
    )

    env_builder = EnvironmentBuilder(env_name, env_params)
    logger.info('Environment is imported')

    exp = BenchmarkExperiment(agent_builder, env_builder, logger)
    logger.info('BenchmarkExperiment was built successfully')

    start_time = time.time()
    exp.run(
        exec_type='parallel',
        n_runs=10,
        n_epochs=100,
        n_steps=30000,
        n_episodes_test=5,
        max_concurrent_runs=10
    )
    end_time = time.time()
    logger.info('Execution time: {} SEC'.format(end_time-start_time))

    exp.save_report()
    #exp.show_report()





