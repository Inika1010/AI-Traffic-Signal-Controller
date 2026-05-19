# import os
# import sys
# import traci
# import time

# # --- CONFIGURATION ---
# SUMO_CONFIG = "osm.sumocfg" 
# TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"

# def run():
#     print(">>> STARTING STATIC (DUMB) SYSTEM DEMO...")
#     sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    
#     if 'SUMO_HOME' in os.environ:
#         sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

#     traci.start(sumo_cmd)
    
#     # Create Ambulance Type
#     try:
#         traci.vehicletype.copy("DEFAULT_VEHTYPE", "amb_type")
#     except:
#         pass # If default fails, we set attributes anyway
    
#     traci.vehicletype.setLength("amb_type", 7.0)
#     traci.vehicletype.setMaxSpeed("amb_type", 30.0)
#     traci.vehicletype.setVehicleClass("amb_type", "emergency")
#     traci.vehicletype.setShapeClass("amb_type", "emergency")
#     traci.vehicletype.setColor("amb_type", (255, 0, 0)) # Red

#     step = 0
#     ambulance_id = None
    
#     # FIXED TIMER SETUP
#     # We use a very long cycle to ensure the ambulance waits a long time
#     phase_duration = [50, 4, 50, 4] 
#     phase_index = 0
#     last_switch_step = 0

#     while step < 2000:
#         # --- 1. THE "RED LIGHT HUNTER" LOGIC ---
#         # We wait until step 100 to let traffic build up.
#         # Then we look for a car that is STOPPED (Speed < 0.5).
#         if ambulance_id is None and step > 100:
#             veh_list = traci.vehicle.getIDList()
#             for veh in veh_list:
#                 # Check if this car is stopped at the light
#                 if traci.vehicle.getSpeed(veh) < 0.5:
#                     # Check if it is actually at our intersection
#                     lane = traci.vehicle.getLaneID(veh)
#                     if lane in traci.trafficlight.getControlledLanes(TL_ID):
#                         # BINGO! Found a stuck car. Make it the ambulance.
#                         target = veh
#                         ambulance_id = target
#                         print(f"\n>>> 🚑 FOUND STOPPED CAR '{target}' -> TRANSFORMING TO AMBULANCE!")
                        
#                         try:
#                             traci.vehicle.setType(target, "amb_type")
#                             traci.vehicle.setColor(target, (255, 0, 0))
#                             traci.vehicle.setShapeClass(target, "emergency")
                            
#                             # Focus Camera so you see it stuck
#                             traci.gui.trackVehicle("View #0", target)
#                             traci.gui.setZoom("View #0", 1000)
#                         except:
#                             ambulance_id = None 
#                         break # Stop looking, we found one

#         # --- 2. STATIC TIMER LOGIC (The Failure) ---
#         current_time_in_phase = step - last_switch_step
        
#         # Check if ambulance is stuck
#         if ambulance_id and ambulance_id in traci.vehicle.getIDList():
#             speed = traci.vehicle.getSpeed(ambulance_id)
#             if speed < 1.0:
#                 # Print clearly for the mentor
#                 print(f"[{step}] 🚨 AMBULANCE STUCK ON RED! Timer says: 'WAIT 40 SECONDS!'")
            
#         # Standard Fixed Logic: Only switch when time is up
#         if current_time_in_phase >= phase_duration[phase_index]:
#             phase_index += 1
#             if phase_index >= len(phase_duration):
#                 phase_index = 0
            
#             traci.trafficlight.setPhase(TL_ID, phase_index)
#             last_switch_step = step
#             print(f"[{step}] Timer Logic: Switching Phase to {phase_index}")

#         traci.simulationStep()
#         step += 1
        
#     traci.close()

# if __name__ == "__main__":
#     run()




import os
import sys
import traci
import time

# --- CONFIGURATION ---
SUMO_CONFIG = "osm.sumocfg" 
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"

def run():
    print(">>> STARTING FINAL STATIC FAIL DEMO...")
    sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG, "--start", "--quit-on-end"]
    
    if 'SUMO_HOME' in os.environ:
        sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))

    traci.start(sumo_cmd)
    
    # 1. SETUP AMBULANCE
    try:
        traci.vehicletype.copy("DEFAULT_VEHTYPE", "amb_type")
    except:
        pass
    traci.vehicletype.setLength("amb_type", 7.0)
    traci.vehicletype.setMaxSpeed("amb_type", 40.0) 
    traci.vehicletype.setVehicleClass("amb_type", "emergency")
    traci.vehicletype.setShapeClass("amb_type", "emergency")
    traci.vehicletype.setColor("amb_type", (255, 0, 0)) # Force Red

    step = 0
    ambulance_spawned = False
    ambulance_id = "AMBULANCE_FAIL"
    
    # --- 2. THE FIX IS HERE ---
    # Phase 2 was Green for you. So we use Phase 0.
    # Phase 0 is usually Vertical Green (which means LEFT LANE RED).
    current_phase = 0 
    
    # Force the light immediately
    traci.trafficlight.setPhase(TL_ID, current_phase)
    
    # Hold this Red light for 120 seconds
    red_timer = 120 

    while step < 3000:
        
        # --- 3. FORCE RED LIGHT LOGIC ---
        if red_timer > 0:
            traci.trafficlight.setPhase(TL_ID, current_phase) # KEEP IT PHASE 0
            red_timer -= 1
            
            if step % 10 == 0 and ambulance_spawned:
                 print(f"[{step}] ⏳ Ambulance waiting at RED... Time left: {red_timer}s")
        else:
            # Timer finished! Now we switch to let it pass (Phase 2)
            if step % 40 == 0:
                 traci.trafficlight.setPhase(TL_ID, 2) 

        # --- 4. SPAWN AMBULANCE (Step 10) ---
        if step == 10:
            route_list = traci.route.getIDList()
            if len(route_list) > 0:
                # We target the route from your screenshot (Left Lane)
                # Usually the first route in the list
                target_route = route_list[0] 
                
                print(f"\n>>> 🔴 TRAP SET (PHASE 0)! LEFT LANE SHOULD BE RED!")
                try:
                    traci.vehicle.add(ambulance_id, target_route, typeID="amb_type")
                    traci.vehicle.setColor(ambulance_id, (255, 0, 0)) # Ensure it's Red
                    ambulance_spawned = True
                except:
                    print("Spawn error...")

        # --- 5. VISUAL CONFIRMATION ---
        if ambulance_spawned and ambulance_id in traci.vehicle.getIDList():
            speed = traci.vehicle.getSpeed(ambulance_id)
            if speed < 0.5:
                 if step % 20 == 0:
                    print(f">>> 🚨 AMBULANCE IS STUCK! (Success)")

        traci.simulationStep()
        step += 1
        
    traci.close()

if __name__ == "__main__":
    run()








