import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from collections import deque
import random

# Load the dataset
df = pd.read_csv('system_metrics.csv')

# Initialize a new column for the number of VMs
df['num_vms'] = 6  # Starting number of VMs

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0   # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma * np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

def run():
    agent = DQNAgent(state_size=4, action_size=2)  # Adjust these values as needed
    batch_size = 32
    episodes = 10  # Control the number of episodes

    for episode in range(episodes):
        total_reward = 0
        for index, row in df.iterrows():
            state = np.array([[row['Throughput'], row['Latency'], row['CPU Usage'], row['Memory Usage']]])
            action = agent.act(state)
            next_state = state  # This should ideally be the next actual state
            reward = row['Throughput'] - row['Latency'] - row['CPU Usage'] - row['Memory Usage']
            done = index == df.index[-1]
            agent.remember(state, action, reward, next_state, done)
            total_reward += reward

            if len(agent.memory) > batch_size:
                agent.replay(batch_size)

            # Update and print status
            df.loc[index, 'num_vms'] = 6 + action
            print(f"Episode {episode+1}, Step {index+1}, Total Reward: {total_reward}")

        if episode % 10 == 0:  # Save every 10 episodes
            df.to_csv('updated_system_metrics.csv', index=False)

if __name__ == '__main__':
    run()
