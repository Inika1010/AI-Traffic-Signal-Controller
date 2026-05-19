import os
import sys
import numpy as np
import traci
import random

# Import Deep Learning Libraries
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam

# --- CONFIGURATION ---
SUMO_CMD = ["sumo", "-c", "osm.sumocfg"]  # Run without GUI for faster training
# SUMO_CMD = ["sumo-gui", "-c", "osm.sumocfg"] # Uncomment to see it happen (slower)

# PASTE YOUR EXACT TRAFFIC LIGHT ID HERE
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"

# Simulation settings
MAX_STEPS = 1000  # Seconds per episode
EPOCHS = 10       # Number of times to train (keep small for testing)

# --- THE AI BRAIN (DQN MODEL) ---
def build_model(input_size, output_size):
    model = Sequential([
        Input(shape=(input_size,)),     # Explicit Input layer
        Dense(32, activation='relu'),   # Hidden layer 1
        Dense(32, activation='relu'),   # Hidden layer 2
        Dense(output_size, activation='linear') # Output: Q-values for actions
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

# --- STATE: READ THE TRAFFIC ---
def get_state(tl_id):
    """
    Returns the number of waiting cars on lanes controlled by this light.
    """
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    # Get unique lanes (sometimes they are duplicated)
    unique_lanes = list(set(lanes))
    
    # Count waiting cars on these lanes
    queue_length = 0
    for lane in unique_lanes:
        queue_length += traci.lane.getLastStepHaltingNumber(lane)
    
    # Also get the current phase ID (0, 1, 2, or 3)
    phase = traci.trafficlight.getPhase(tl_id)
    
    # Return as a numpy array for the AI
    return np.array([queue_length, phase])

# --- MAIN TRAINING LOOP ---
if __name__ == "__main__":
    
    # 1. Setup Environment
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
    else:
        sys.exit("Please set SUMO_HOME")

    print("--- STARTING TRAINING ---")
    
    # Initialize Model
    # Input: 2 values (Queue Length, Current Phase)
    # Output: 2 actions (0 = Keep Phase, 1 = Switch Phase)
    brain = build_model(2, 2)
    
    for epoch in range(EPOCHS):
        print(f"Epoch {epoch+1}/{EPOCHS}")
        
        try:
            traci.start(SUMO_CMD)
        except traci.TraCIException:
             # Sometimes Sumo fails to close properly, retry
            traci.close()
            traci.start(SUMO_CMD)

        step = 0
        total_reward = 0
        
        # Initial State
        state = get_state(TL_ID)
        state = np.reshape(state, [1, 2]) # Format for Keras

        while step < MAX_STEPS:
            # 1. AI Decides Action
            # If phase is Yellow (1 or 3), we MUST wait. No choice.
            current_phase = traci.trafficlight.getPhase(TL_ID)
            
            action = 0
            if current_phase == 1 or current_phase == 3:
                # Yellow light: Do nothing, just wait
                action = 0 
            else:
                # Green light: Ask AI
                if random.uniform(0, 1) < 0.2: # Exploration (20% random)
                    action = random.choice([0, 1])
                else:
                    q_values = brain.predict(state, verbose=0)
                    action = np.argmax(q_values[0])

            # 2. Execute Action
            # Action 0 = Stay. Action 1 = Switch to next phase.
            if action == 1 and (current_phase == 0 or current_phase == 2):
                traci.trafficlight.setPhase(TL_ID, current_phase + 1) # Switch to Yellow
            
            # Step the simulation
            traci.simulationStep()
            step += 1

            # 3. Calculate Reward
            # Reward = Negative Queue Length (We want close to 0 queue)
            next_state = get_state(TL_ID)
            next_state = np.reshape(next_state, [1, 2])
            
            queue = next_state[0][0]
            reward = -queue 
            total_reward += reward

            # 4. Train the Brain (Experience Replay - Simplified)
            target = brain.predict(state, verbose=0)
            target[0][action] = reward + 0.95 * np.max(brain.predict(next_state, verbose=0))
            brain.fit(state, target, epochs=1, verbose=0)

            state = next_state
            
        print(f"  -> Total Reward (Traffic Flow Score): {total_reward}")
        traci.close()

    print("--- TRAINING FINISHED ---")
    print("Saving model as 'traffic_model.keras'...")
    brain.save('traffic_model.keras')