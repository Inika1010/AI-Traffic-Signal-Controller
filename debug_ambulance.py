import os
import sys
import numpy as np
import traci
import random
import time

# --- CONFIGURATION ---
SUMO_CONFIG = "osm.sumocfg" 
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"
MIN_GREEN_TIME = 10 

def get_state(tl_id):
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    queue = 0
    for lane in set(lanes):
        queue += traci.lane.getLastStepHaltingNumber(lane)
    phase = traci.trafficlight.getPhase(tl_id)
    return np.array([[queue, phase]])

def run():
    print(">>> 1. INITIALIZING SIMULATION...")
    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

    print(">>> 2. LOADING AI BRAIN...")
    brain = None
    try:
        from tensorflow.keras.models import load_model
        if os.path.exists('traffic_model.keras'):
            brain = load_model('traffic_model.keras')
            print("   > SUCCESS: 'traffic_model.keras' loaded.")
        else:
            print("   > WARNING: Model file not found. Running in demo mode without brain.")
    except Exception as e:
        print(f"   > WARNING: Could not load Keras/TensorFlow. Error: {e}")

    print(">>> 3. LAUNCHING GUI...")
    traci.start(sumo_cmd)
    
    # --- FIX IS HERE: CREATE THE TYPE FIRST ---
    # We must copy a default type to create 'amb_type' before modifying it
    traci.vehicletype.copy("DEFAULT_VEHTYPE", "amb_type")
    
    # Now we can safely modify it
    traci.vehicletype.setLength("amb_type", 7.0)
    traci.vehicletype.setMaxSpeed("amb_type", 30.0)
    traci.vehicletype.setVehicleClass("amb_type", "emergency")
    traci.vehicletype.setShapeClass("amb_type", "emergency")
    traci.vehicletype.setColor("amb_type", (255, 0, 0)) # Red
    
    step = 0
    steps_since_switch = 0
    ambulance_id = None
    ambulance_active = False
    
    print(">>> SIMULATION RUNNING. WAITING FOR TRAFFIC...")

    while step < 2000:
        # --- PHASE A: FIND A VICTIM CAR TO TRANSFORM ---
        if ambulance_id is None and step > 50:
            veh_list = traci.vehicle.getIDList()
            if len(veh_list) > 0:
                target = veh_list[0]
                ambulance_id = target
                ambulance_active = True
                print(f"\n>>> 🚑 TRANSFORMING VEHICLE '{target}' INTO AMBULANCE!")
                try:
                    traci.vehicle.setType(target, "amb_type")
                    traci.vehicle.setColor(target, (255, 0, 0))
                    traci.vehicle.setShapeClass(target, "emergency")
                    traci.gui.trackVehicle("View #0", target)
                    traci.gui.setZoom("View #0", 1000)
                except:
                    ambulance_id = None 

        # --- PHASE B: CONTROL LOGIC ---
        action = 0 
        current_phase = traci.trafficlight.getPhase(TL_ID)
        
        ambulance_is_approaching = False
        
        if ambulance_active and ambulance_id in traci.vehicle.getIDList():
            amb_lane = traci.vehicle.getLaneID(ambulance_id)
            controlled_lanes = traci.trafficlight.getControlledLanes(TL_ID)
            
            if amb_lane in controlled_lanes:
                ambulance_is_approaching = True
                speed = traci.vehicle.getSpeed(ambulance_id)
                
                if speed < 2.0: 
                    print(f"[{step}] 🚨 AMBULANCE STUCK! FORCE GREEN LIGHT! 🚨")
                    action = 1 
                else:
                    action = 0 
                    steps_since_switch = 0 

        # --- PHASE C: EXECUTE ---
        if not ambulance_is_approaching and brain:
            state = get_state(TL_ID)
            q = brain.predict(state, verbose=0)
            ai_action = np.argmax(q[0])
            
            if current_phase % 2 != 0: 
                action = 0 
            elif steps_since_switch < MIN_GREEN_TIME:
                action = 0 
            else:
                action = ai_action 

        if action == 1:
            # Safe phase switching logic
            if current_phase < 3:
                traci.trafficlight.setPhase(TL_ID, current_phase + 1)
            else:
                traci.trafficlight.setPhase(TL_ID, 0)
            steps_since_switch = 0
        else:
            steps_since_switch += 1

        traci.simulationStep()
        step += 1
        
    print(">>> SIMULATION FINISHED.")
    traci.close()

if __name__ == "__main__":
    run()