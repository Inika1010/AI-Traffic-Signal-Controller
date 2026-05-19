import os
import sys
import traci

SUMO_CONFIG_FILE = "osm.sumocfg"
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please set SUMO_HOME")

# Start simulation in the background (no GUI needed for this check)
sumoCmd = ["sumo", "-c", SUMO_CONFIG_FILE] 
traci.start(sumoCmd)

print("--- TRAFFIC LIGHT INSPECTION ---")

# 1. Get the ID of the traffic light
# The map might have multiple, but we usually want the main one at the center.
tl_ids = traci.trafficlight.getIDList()
print(f"Found Traffic Lights: {tl_ids}")

# We will assume the first one in the list is the main junction
if len(tl_ids) > 0:
    main_tl_id = tl_ids[0]
    print(f"\nAnalyzing Traffic Light ID: {main_tl_id}")

    # 2. Get the Logic (The Phases)
    # A 'Phase' is a specific combination of Green/Red lights (e.g., "North-South Green")
    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(main_tl_id)[0]
    
    print(f"Number of Phases: {len(logic.phases)}")
    
    for i, phase in enumerate(logic.phases):
        print(f"  Phase {i}: Duration={phase.duration}s | State='{phase.state}'")
        # 'State' is a string like "GrGr", where G=Green, r=Red.
else:
    print("No traffic lights found! Did you check the box in the wizard?")

traci.close()