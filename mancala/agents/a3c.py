"""Agent with uses A3C trained network"""

import random

import torch
import torch.nn.functional as F
from torch.autograd import Variable

from mancala.game import Game
from mancala.env import MancalaEnv
from mancala.agents.agent import Agent
from mancala.trainers.a3c_model import ActorCritic


class AgentA3C(Agent):
    '''Agent which leverages Actor Critic Learning'''

    def __init__(self,
                 model_path,
                 dtype,
                 seed=451):
        self._seed = seed
        self._idx = 0
        self._dtype = dtype
        self.env = MancalaEnv(seed)
        state = self.env.reset()

        self._model = ActorCritic(
            state.shape[0], self.env.action_space).type(dtype)
        self._model.load_state_dict(torch.load(model_path))

    def _move(self, game):
        '''Return move which ends in score hole'''
        assert not game.over()
        self._idx += 1
        game_clone, rot_flag = game.clone_turn()
        move_options = Agent.valid_indices(game_clone)

        state = self.env.force(game_clone)
        state = torch.from_numpy(state).type(self._dtype)
        cx = Variable(torch.zeros(1, 400).type(self._dtype), volatile=True)
        hx = Variable(torch.zeros(1, 400).type(self._dtype), volatile=True)

        _, logit, (hx, cx) = self._model(
            (Variable(state.unsqueeze(0), volatile=True), (hx, cx)))
        prob = F.softmax(logit)
        scores = [(action, score) for action, score in enumerate(
            prob[0].data.tolist()) if action in move_options]
        scores_sorted = sorted(scores, key=lambda t: t[1], reverse=True)
        final_move = scores_sorted[0][0]

        return Game.rotate_board(rot_flag, final_move)
