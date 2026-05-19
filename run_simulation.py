import os
import sys
import traci # The library that connects Python to SUMO

# 1. Configuration
# We need to point to the config file you just generated
SUMO_CONFIG_FILE = "osm.sumocfg" 

# 2. Check Environment
# This ensures we can find the SUMO software
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Error: Please set the environment variable 'SUMO_HOME'")

# 3. Define the Start Command
# This tells Python: "Open the SUMO GUI and load my map"
sumoCmd = ["sumo-gui", "-c", SUMO_CONFIG_FILE, "--start"]

# 4. The Main Loop
print("--- Starting Simulation ---")
traci.start(sumoCmd) # This opens the window

step = 0
while step < 500: # Run for 500 simulation seconds
    traci.simulationStep() # This effectively clicks the "Next Step" button
    
    # Every 100 steps, let's print a message to the console
    if step % 100 == 0:
        print(f"Simulation is running... Step {step}")
        
    step += 1

traci.close() # Close the connection
print("--- Simulation Finished ---")