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
# Run without GUI (Headless) to make it 20% faster
#SUMO_CMD = ["sumo", "-c", "osm.sumocfg"] 
# Add teleport options to prevent gridlock freezing the PC
SUMO_CMD = ["sumo", "-c", "osm.sumocfg", "--time-to-teleport", "150"]
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"

MAX_STEPS = 500  
EPOCHS = 50       # Increased for Heavy Traffic
BATCH_SIZE = 32
MEMORY_SIZE = 2000

# --- THE AI BRAIN ---
def build_model(input_size, output_size):
    model = Sequential([
        Input(shape=(input_size,)),
        Dense(64, activation='relu'),    # Bigger brain (64 neurons)
        Dense(64, activation='relu'),
        Dense(output_size, activation='linear')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

# --- STATE: READ THE TRAFFIC ---
def get_state(tl_id):
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    unique_lanes = list(set(lanes))
    queue_length = 0
    for lane in unique_lanes:
        queue_length += traci.lane.getLastStepHaltingNumber(lane)
    
    # Inputs: [Queue Length, Current Phase ID]
    phase = traci.trafficlight.getPhase(tl_id)
    return np.array([queue_length, phase])

# --- MAIN TRAINING LOOP ---
if __name__ == "__main__":
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    
    print(f"--- STARTING HEAVY TRAFFIC TRAINING ({EPOCHS} Epochs) ---")
    
    # 1. Setup Brain
    brain = build_model(2, 2)
    memory = [] # Experience Replay
    epsilon = 1.0 # Exploration rate (Start curious)
    epsilon_min = 0.01
    epsilon_decay = 0.95

    for epoch in range(EPOCHS):
        print(f"Epoch {epoch+1}/{EPOCHS}")
        
        try:
            traci.start(SUMO_CMD)
        except:
            traci.close()
            traci.start(SUMO_CMD)

        step = 0
        total_reward = 0
        state = get_state(TL_ID)
        state = np.reshape(state, [1, 2])

        while step < MAX_STEPS:
            current_phase = traci.trafficlight.getPhase(TL_ID)
            
            # Action Decision
            action = 0
            if current_phase in [1, 3]: # Yellow
                action = 0
            else:
                if np.random.rand() <= epsilon:
                    action = random.choice([0, 1]) # Explore
                else:
                    q_values = brain.predict(state, verbose=0)
                    action = np.argmax(q_values[0]) # Exploit

            # Execute
            if action == 1 and current_phase in [0, 2]:
                traci.trafficlight.setPhase(TL_ID, current_phase + 1)
            
            traci.simulationStep()
            step += 1

            # Get New State & Reward
            next_state = get_state(TL_ID)
            next_state = np.reshape(next_state, [1, 2])
            
            queue = next_state[0][0]
            reward = -queue # Penalty for every waiting car
            total_reward += reward

            # Remember
            memory.append((state, action, reward, next_state))
            if len(memory) > MEMORY_SIZE:
                memory.pop(0)

            state = next_state

            # Train (Replay)
            if len(memory) > BATCH_SIZE:
                minibatch = random.sample(memory, BATCH_SIZE)
                for state_m, action_m, reward_m, next_state_m in minibatch:
                    target = reward_m
                    if not False: # not done
                        target = (reward_m + 0.95 * np.amax(brain.predict(next_state_m, verbose=0)[0]))
                    target_f = brain.predict(state_m, verbose=0)
                    target_f[0][action_m] = target
                    brain.fit(state_m, target_f, epochs=1, verbose=0)

        # End of Epoch
        traci.close()
        print(f"  -> Total Reward: {total_reward}")
        
        # Save every 5 epochs
        if (epoch + 1) % 5 == 0:
            brain.save(f'traffic_model_epoch_{epoch+1}.keras')
            print(f"  [Saved Backup: traffic_model_epoch_{epoch+1}.keras]")

        # Reduce exploration (Get smarter over time)
        if epsilon > epsilon_min:
            epsilon *= epsilon_decay

    print("--- TRAINING FINISHED ---")
    brain.save('traffic_model.keras') # Final save