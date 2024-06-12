import numpy as np
import pandas as pd
from collections import deque
import random
from networks import myLSTM
import torch
import torch.nn as nn

# Define the Double DQN Agent
class DDQNAgent:
    def __init__(self, state_size, action_size, sequence_length):
        self.state_size = state_size
        self.action_size = action_size
        self.sequence_length = sequence_length
        self.memory = deque(maxlen=500)
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.online_model = myLSTM(state_size, 128, 3, action_size)
        self.target_model = myLSTM(state_size, 128, 3, action_size)
        self.update_target_model()

        self.optimizer = torch.optim.Adam(self.online_model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def update_target_model(self):
        self.target_model.load_state_dict(self.online_model.state_dict())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, verbose=False):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state = np.array(state)
        state = np.reshape(state, (1, self.sequence_length, self.state_size))

        state = torch.tensor(state, dtype=torch.float32)

        self.online_model.eval()
        with torch.no_grad():
            act_values = self.online_model.forward(state)

        return torch.argmax(act_values).item()


    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        import time
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_state = np.array([next_state])
                next_state = np.reshape(next_state, (1, self.sequence_length, self.state_size))
                next_state = torch.tensor(next_state, dtype=torch.float32)
                # prediction of next state
                target = (reward + self.gamma * torch.max(self.target_model.forward(next_state)))

            state = np.array([state])
            state = np.reshape(state, (1, self.sequence_length, self.state_size))
            state = torch.tensor(state, dtype=torch.float32)
            start = time.time()

            # print(target, 'target')

            self.online_model.eval()
            with torch.no_grad():
                target_f = self.online_model.forward(state)

                target_f[0][action] = target
            
            self.online_model.train()
            self.online_model.zero_grad()
            target = self.online_model.forward(state)
            loss = self.criterion(target_f.detach(), target)
            loss.backward()
            print(loss)
            self.optimizer.step()
            # print("Time taken for one replay step: ", time.time() - start)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        self.update_target_model()
