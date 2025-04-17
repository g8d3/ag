
import pytest
from cua4_rl import QLearning, SARSA, PPO

def test_qlearning_update():
    algo = QLearning()
    state = "initial"
    action = "improve_modularity"
    reward = 0.8
    next_state = "score_80"
    algo.update(state, action, reward, next_state)
    assert algo.q_table[state][action] > 0

def test_sarsa_update():
    algo = SARSA()
    state = "initial"
    action = "add_features"
    reward = 0.7
    next_state = "score_70"
    next_action = "fix_bugs"
    algo.update(state, action, reward, next_state, next_action)
    assert algo.q_table[state][action] > 0

def test_ppo_update():
    algo = PPO()
    state = "initial"
    action = "fix_bugs"
    reward = 0.9
    next_state = "score_90"
    algo.update(state, action, reward, next_state)
    assert algo.policy[state][action] > 0.33
