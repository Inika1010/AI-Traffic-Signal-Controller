# import os
# import sys
# import numpy as np
# import traci
# import random
# import time

# # --- CONFIGURATION ---
# SUMO_CONFIG = "osm.sumocfg" 
# TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"
# MIN_GREEN_TIME = 10 

# def get_state(tl_id):
#     lanes = traci.trafficlight.getControlledLanes(tl_id)
#     queue = 0
#     for lane in set(lanes):
#         queue += traci.lane.getLastStepHaltingNumber(lane)
#     phase = traci.trafficlight.getPhase(tl_id)
#     return np.array([[queue, phase]])

# def run():
#     print(">>> 1. INITIALIZING SIMULATION...")
#     sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    
#     if 'SUMO_HOME' in os.environ:
#         sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

#     # Load AI Model
#     brain = None
#     try:
#         from tensorflow.keras.models import load_model
#         if os.path.exists('traffic_model.keras'):
#             brain = load_model('traffic_model.keras')
#             print("   > AI Model Loaded.")
#     except Exception as e:
#         print(f"   > Warning: Model not found ({e})")

#     traci.start(sumo_cmd)
    
#     # Create Ambulance Type (Red, Fast, Emergency)
#     # We copy the default type first to avoid the "Unknown Type" error
#     try:
#         traci.vehicletype.copy("DEFAULT_VEHTYPE", "amb_type")
#     except:
#         # Fallback if DEFAULT_VEHTYPE doesn't exist, try creating fresh
#         pass
        
#     traci.vehicletype.setLength("amb_type", 7.0)
#     traci.vehicletype.setMaxSpeed("amb_type", 30.0)
#     traci.vehicletype.setVehicleClass("amb_type", "emergency")
#     traci.vehicletype.setShapeClass("amb_type", "emergency")
#     traci.vehicletype.setColor("amb_type", (255, 0, 0)) # Red
    
#     step = 0
#     steps_since_switch = 0
#     ambulance_id = None
#     ambulance_active = False
    
#     print(">>> SIMULATION RUNNING...")

#     while step < 2000:
#         # --- PHASE A: TRANSFORM CAR TO AMBULANCE ---
#         if ambulance_id is None and step > 50:
#             veh_list = traci.vehicle.getIDList()
#             if len(veh_list) > 0:
#                 target = veh_list[0]
#                 ambulance_id = target
#                 ambulance_active = True
#                 print(f"\n>>> 🚑 TRANSFORMING VEHICLE '{target}' INTO AMBULANCE!")
                
#                 try:
#                     traci.vehicle.setType(target, "amb_type")
#                     traci.vehicle.setColor(target, (255, 0, 0))
#                     traci.vehicle.setShapeClass(target, "emergency")
#                     # NO ZOOM / NO TRACKING HERE
#                 except:
#                     ambulance_id = None 

#         # --- PHASE B: PRIORITY LOGIC ---
#         action = 0 
#         current_phase = traci.trafficlight.getPhase(TL_ID)
#         ambulance_is_approaching = False
        
#         if ambulance_active and ambulance_id in traci.vehicle.getIDList():
#             amb_lane = traci.vehicle.getLaneID(ambulance_id)
#             controlled_lanes = traci.trafficlight.getControlledLanes(TL_ID)
            
#             if amb_lane in controlled_lanes:
#                 ambulance_is_approaching = True
#                 speed = traci.vehicle.getSpeed(ambulance_id)
                
#                 if speed < 2.0: 
#                     print(f"[{step}] 🚨 AMBULANCE BLOCKED! FORCE GREEN! 🚨")
#                     action = 1 # Force switch
#                 else:
#                     action = 0 # Keep moving (Don't let AI switch to Red)
#                     steps_since_switch = 0 

#         # --- PHASE C: AI LOGIC ---
#         if not ambulance_is_approaching and brain:
#             state = get_state(TL_ID)
#             q = brain.predict(state, verbose=0)
#             ai_action = np.argmax(q[0])
            
#             # Normal AI Rules
#             if current_phase % 2 != 0: 
#                 action = 0 
#             elif steps_since_switch < MIN_GREEN_TIME:
#                 action = 0 
#             else:
#                 action = ai_action 

#         # Apply Action
#         if action == 1:
#             if current_phase < 3:
#                 traci.trafficlight.setPhase(TL_ID, current_phase + 1)
#             else:
#                 traci.trafficlight.setPhase(TL_ID, 0)
#             steps_since_switch = 0
#         else:
#             steps_since_switch += 1

#         traci.simulationStep()
#         step += 1
        
#     print(">>> SIMULATION FINISHED.")
#     traci.close()

# if __name__ == "__main__":
#     run()









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

# --- HELPER: GET QUEUE ON GREEN LANES ---
def get_green_queue(tl_id):
    """
    Returns the number of cars waiting on lanes that currently have a Green light.
    """
    # Get the string like "GrGr" showing which lanes are green
    phase_state = traci.trafficlight.getRedYellowGreenState(tl_id)
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    
    waiting_on_green = 0
    
    # We loop through all lanes. If the lane has a 'G' or 'g', we count its cars.
    # Note: len(phase_state) might not match len(lanes) perfectly in complex maps,
    # but for standard junctions, it maps 1-to-1 or by index.
    for i, lane in enumerate(lanes):
        if i < len(phase_state):
            signal = phase_state[i]
            if signal == 'G' or signal == 'g':
                # This lane is Green. Check if cars are stuck on it.
                waiting_on_green += traci.lane.getLastStepHaltingNumber(lane)
                
    return waiting_on_green

def get_state(tl_id):
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    queue = 0
    for lane in set(lanes):
        queue += traci.lane.getLastStepHaltingNumber(lane)
    phase = traci.trafficlight.getPhase(tl_id)
    return np.array([[queue, phase]])

def run():
    print(">>> 1. INITIALIZING SIMULATION (WITH QUEUE CLEARANCE)...")
    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

    # Load AI Model
    brain = None
    try:
        from tensorflow.keras.models import load_model
        if os.path.exists('traffic_model.keras'):
            brain = load_model('traffic_model.keras')
            print("   > AI Model Loaded.")
    except Exception as e:
        print(f"   > Warning: Model not found ({e})")

    traci.start(sumo_cmd)
    
    # Setup Ambulance Type
    try:
        traci.vehicletype.copy("DEFAULT_VEHTYPE", "amb_type")
    except:
        pass  
    traci.vehicletype.setLength("amb_type", 7.0)
    traci.vehicletype.setMaxSpeed("amb_type", 30.0)
    traci.vehicletype.setVehicleClass("amb_type", "emergency")
    traci.vehicletype.setShapeClass("amb_type", "emergency")
    traci.vehicletype.setColor("amb_type", (255, 0, 0)) # Red
    
    step = 0
    steps_since_switch = 0
    ambulance_id = None
    ambulance_active = False
    
    print(">>> SIMULATION RUNNING...")

    while step < 2000:
        # --- PHASE A: TRANSFORM CAR TO AMBULANCE ---
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
                except:
                    ambulance_id = None 

        # --- PHASE B: PRIORITY LOGIC (Highest Priority) ---
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
                    print(f"[{step}] 🚨 AMBULANCE BLOCKED! FORCE GREEN! 🚨")
                    action = 1 # Force switch
                else:
                    action = 0 # Keep moving (Don't let AI switch to Red)
                    steps_since_switch = 0 

        # --- PHASE C: AI LOGIC + QUEUE CLEARANCE ---
        if not ambulance_is_approaching and brain:
            state = get_state(TL_ID)
            q = brain.predict(state, verbose=0)
            ai_action = np.argmax(q[0])
            
            # --- THE FIX: CHECK IF CARS ARE STILL STUCK ON GREEN ---
            cars_on_green = get_green_queue(TL_ID)
            
            if current_phase % 2 != 0: 
                action = 0 # Yellow -> Must wait
            elif steps_since_switch < MIN_GREEN_TIME:
                action = 0 # Min Time -> Must wait
            elif cars_on_green > 4:
                # RULE: If > 4 cars are still waiting on the green lane,
                # we EXTEND the green light. We ignore the AI's wish to switch.
                # print(f"[{step}] Extending Green... {cars_on_green} cars remaining.")
                action = 0 
            else:
                # Queue is small (<= 4 cars), so we let the AI decide
                action = ai_action 

        # Apply Action
        if action == 1:
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