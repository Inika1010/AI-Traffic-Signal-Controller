import os
import sys
import traci

# 1. Setup
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please set SUMO_HOME")

# YOUR ID
TL_ID = "GS_cluster_381529383_4330817110_4330817116_4330817131"

def run_dumb_static():
    print("--- RUNNING DUMB STATIC SIMULATION ---")
    sumo_cmd = ["sumo", "-c", "osm.sumocfg"] 
    traci.start(sumo_cmd)
    
    # Force a "Fixed Time" program
    # This logic forces the light to stay Green for 45s, then Yellow 4s
    # regardless of traffic. This simulates a "dumb" city light.
    
    step = 0
    phase_timer = 0
    current_phase_index = 0
    
    # 0=Green, 1=Yellow, 2=Green, 3=Yellow
    # We force: 45s Green, 4s Yellow, 45s Green, 4s Yellow
    durations = [45, 4, 45, 4] 
    
    queue_history = []

    while step < 1000:
        # Measure Queue
        lanes = traci.trafficlight.getControlledLanes(TL_ID)
        total_queue = 0
        for lane in set(lanes):
            total_queue += traci.lane.getLastStepHaltingNumber(lane)
        queue_history.append(total_queue)
        
        # Manually Control the Light to be "Dumb"
        traci.trafficlight.setPhase(TL_ID, current_phase_index)
        
        phase_timer += 1
        if phase_timer >= durations[current_phase_index]:
            # Time to switch phase
            phase_timer = 0
            current_phase_index += 1
            if current_phase_index > 3:
                current_phase_index = 0
                
        traci.simulationStep()
        step += 1
        
    traci.close()
    return queue_history

if __name__ == "__main__":
    # We just test if it runs
    data = run_dumb_static()
    print(f"Simulation done. Avg Queue: {sum(data)/len(data)}")