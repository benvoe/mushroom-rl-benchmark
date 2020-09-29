import numpy as np
import torch.optim as optim
import torch.nn.functional as F

from mushroom_rl.algorithms.actor_critic import SAC
from mushroom_rl.policy import GaussianTorchPolicy
from mushroom_rl.utils.preprocessors import StandardizationPreprocessor

from mushroom_rl_benchmark.agent import AgentBuilder
from mushroom_rl_benchmark.agent.network import SACActorNetwork as ActorNetwork, SACCriticNetwork as CriticNetwork

class SACBuilder(AgentBuilder):
    """
    Builder Soft Actor-Critic algorithm (SAC).
    """

    def __init__(self, actor_mu_params, actor_sigma_params, actor_optimizer, critic_params, alg_params, n_q_samples=100, n_steps_per_fit=1, preprocessors=[StandardizationPreprocessor]):
        self.actor_mu_params = actor_mu_params
        self.actor_sigma_params = actor_sigma_params
        self.actor_optimizer = actor_optimizer
        self.critic_params = critic_params
        self.alg_params = alg_params
        self.n_q_samples = n_q_samples
        super().__init__(n_steps_per_fit, compute_entropy_with_states=True, preprocessors=preprocessors)

    def build(self, mdp_info):
        actor_input_shape = mdp_info.observation_space.shape
        self.actor_mu_params['input_shape'] = actor_input_shape
        self.actor_mu_params['output_shape'] = mdp_info.action_space.shape
        self.actor_sigma_params['input_shape'] = actor_input_shape
        self.actor_sigma_params['output_shape'] = mdp_info.action_space.shape

        critic_input_shape = (actor_input_shape[0] + mdp_info.action_space.shape[0],)
        self.critic_params["input_shape"] = critic_input_shape
        sac = SAC(mdp_info, self.actor_mu_params, self.actor_sigma_params, self.actor_optimizer, self.critic_params, **self.alg_params)
        print("TARGET_ENTROPY", sac._target_entropy)
        return sac

    def compute_Q(self, agent, states):
        Qs = list()
        for state in states:
            s = np.array([state for i in range(self.n_q_samples)])
            a = np.array([agent.policy.draw_action(state) for i in range(self.n_q_samples)])
            Qs.append(agent._critic_approximator(s, a).mean())
        return np.array(Qs).mean()

    def random_init(self, trial):
        n_features = trial.suggest_categorical('n_features', [32, 64])
        actor_lr = trial.suggest_loguniform('actor_lr', 1e-5, 1e-2)
        critic_lr = trial.suggest_loguniform('critic_lr', 1e-5, 1e-2)

        self.actor_mu_params['n_features'] = n_features
        self.actor_sigma_params['n_features'] = n_features
        self.actor_optimizer['params']['lr'] = actor_lr
        self.critic_params['n_features'] = n_features
        self.critic_params['optimizer']['params']['lr'] = critic_lr
    
    @classmethod
    def default(cls, actor_lr=3e-4, actor_network=ActorNetwork, critic_lr=3e-4, critic_network=CriticNetwork, initial_replay_size=64, max_replay_size=50000, n_features=64, warmup_transitions=100, preprocessors=[StandardizationPreprocessor], target_entropy=None, use_cuda=False):

        actor_mu_params = dict(network=actor_network,
                            n_features=n_features,
                            use_cuda=use_cuda)
        actor_sigma_params = dict(network=actor_network,
                                n_features=n_features,
                                use_cuda=use_cuda)

        actor_optimizer = {'class': optim.Adam,
                        'params': {'lr': actor_lr}}
                        
        critic_params = dict(network=critic_network,
                            optimizer={'class': optim.Adam,
                                        'params': {'lr': critic_lr}},
                            loss=F.mse_loss,
                            n_features=n_features,
                            output_shape=(1,),
                            use_cuda=use_cuda)
        
        alg_params = dict(
            initial_replay_size=initial_replay_size,
            max_replay_size=max_replay_size,
            batch_size=64,
            warmup_transitions=warmup_transitions,
            tau=5e-3,
            lr_alpha=3e-4,
            critic_fit_params=None,
            target_entropy=target_entropy)

        return cls(actor_mu_params, actor_sigma_params, actor_optimizer, critic_params, alg_params, preprocessors=preprocessors)
        