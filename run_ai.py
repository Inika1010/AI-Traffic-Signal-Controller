import os
import sys
import numpy as np
import traci
import tensorflow as tf
from tensorflow.keras.models import load_model

# --- CONFIGURATION ---
SUMO_CMD = ["sumo-gui", "-c", "osm.sumocfg"] # We want the GUI now!
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131" # Your ID

# --- HELPER FUNCTION ---
def get_state(tl_id):
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    unique_lanes = list(set(lanes))
    queue_length = 0
    for lane in unique_lanes:
        queue_length += traci.lane.getLastStepHaltingNumber(lane)
    phase = traci.trafficlight.getPhase(tl_id)
    return np.array([queue_length, phase])

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    # 1. Setup
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

    print("--- LOADING SAVED MODEL ---")
    try:
        brain = load_model('traffic_model.keras')
        print("Model loaded successfully!")
    except:
        sys.exit("Error: Could not load 'traffic_model.keras'. Did you run training?")

    print("--- STARTING AI SIMULATION ---")
    traci.start(SUMO_CMD)
    
    step = 0
    while step < 1000:
        # Get current situation
        state = get_state(TL_ID)
        state = np.reshape(state, [1, 2])
        
        # Ask the AI what to do
        current_phase = traci.trafficlight.getPhase(TL_ID)
        
        if current_phase == 1 or current_phase == 3:
            # Yellow light - must wait
            action = 0
        else:
            # Green light - AI decides
            q_values = brain.predict(state, verbose=0)
            action = np.argmax(q_values[0])
            
        # Execute
        if action == 1 and (current_phase == 0 or current_phase == 2):
            print(f"Step {step}: AI decided to SWITCH the light!")
            traci.trafficlight.setPhase(TL_ID, current_phase + 1)
            
        traci.simulationStep()
        step += 1
        
    traci.close()
    print("--- DEMO FINISHED ---")