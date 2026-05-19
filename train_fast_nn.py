import os
import sys
import numpy as np
import traci
import random
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam

# --- CONFIGURATION ---
# 1. Teleport: Removes stuck cars after 50s so simulation never freezes
SUMO_CMD = ["sumo", "-c", "osm.sumocfg", "--time-to-teleport", "50"] 
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"

MAX_STEPS = 500    # Short episodes for speed
EPOCHS = 15        # 15 epochs is enough to learn basic clearing
BATCH_SIZE = 32
MEMORY_SIZE = 1000
MIN_GREEN_TIME = 10 # CRITICAL: AI must hold green for 10s minimum

# --- BRAIN ---
def build_model(input_size, output_size):
    model = Sequential([
        Input(shape=(input_size,)),
        Dense(32, activation='relu'),
        Dense(32, activation='relu'),
        Dense(output_size, activation='linear')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

# --- STATE ---
def get_state(tl_id):
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    queue_length = 0
    for lane in set(lanes):
        queue_length += traci.lane.getLastStepHaltingNumber(lane)
    phase = traci.trafficlight.getPhase(tl_id)
    return np.array([queue_length, phase])

# --- MAIN ---
if __name__ == "__main__":
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    
    print(f"--- STARTING FAST RL TRAINING ({EPOCHS} Epochs) ---")
    brain = build_model(2, 2)
    memory = []
    epsilon = 1.0 
    epsilon_decay = 0.90 # Decay faster to learn faster

    for epoch in range(EPOCHS):
        print(f"Epoch {epoch+1}/{EPOCHS} ... ", end="")
        sys.stdout.flush() # Force print
        
        try:
            traci.start(SUMO_CMD)
        except:
            traci.close()
            traci.start(SUMO_CMD)

        step = 0
        total_reward = 0
        steps_since_switch = 0 # Timer for Min Green
        
        state = get_state(TL_ID)
        state = np.reshape(state, [1, 2])

        while step < MAX_STEPS:
            current_phase = traci.trafficlight.getPhase(TL_ID)
            
            # --- ACTION LOGIC ---
            action = 0
            
            # Constraint 1: If Yellow, MUST wait
            if current_phase in [1, 3]:
                action = 0 
                steps_since_switch = 0 # Reset timer
            
            # Constraint 2: If Green but too short, MUST wait (Fixes Freezing!)
            elif steps_since_switch < MIN_GREEN_TIME:
                action = 0
                steps_since_switch += 1
            
            # Otherwise: AI Chooses
            else:
                steps_since_switch += 1
                if np.random.rand() <= epsilon:
                    action = random.choice([0, 1])
                else:
                    q_values = brain.predict(state, verbose=0)
                    action = np.argmax(q_values[0])

            # Execute
            if action == 1:
                traci.trafficlight.setPhase(TL_ID, current_phase + 1)
                steps_since_switch = 0 # Reset timer because we switched
            
            traci.simulationStep()
            step += 1

            # Learning
            next_state = get_state(TL_ID)
            next_state = np.reshape(next_state, [1, 2])
            reward = -next_state[0][0] # Reward = Negative Queue
            total_reward += reward

            memory.append((state, action, reward, next_state))
            state = next_state
            
            if len(memory) > MEMORY_SIZE: memory.pop(0)
            if len(memory) > BATCH_SIZE:
                minibatch = random.sample(memory, BATCH_SIZE)
                # Fast training loop
                states = np.array([i[0][0] for i in minibatch])
                next_states = np.array([i[3][0] for i in minibatch])
                targets = brain.predict(states, verbose=0)
                next_qs = brain.predict(next_states, verbose=0)
                
                for i, (_, action_m, reward_m, _) in enumerate(minibatch):
                    targets[i][action_m] = reward_m + 0.9 * np.amax(next_qs[i])
                
                brain.fit(states, targets, epochs=1, verbose=0)

        traci.close()
        print(f"Done. Reward: {total_reward}")
        
        if epsilon > 0.01: epsilon *= epsilon_decay
        
        # Save occasionally
        if (epoch+1) % 5 == 0:
            brain.save('traffic_model.keras')

    print("--- SAVING FINAL MODEL ---")
    brain.save('traffic_model.keras')