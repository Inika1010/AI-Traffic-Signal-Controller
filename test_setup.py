import os
import sys
import shutil

print("--- PHASE 1 DIAGNOSTIC ---")

# 1. Check if Windows knows where SUMO is (You just fixed this!)
if 'SUMO_HOME' in os.environ:
    print(f"[SUCCESS] SUMO_HOME is set to: {os.environ['SUMO_HOME']}")
    # Add SUMO tools to Python's path so we can import them
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    print("[FAIL] SUMO_HOME is missing.")

# 2. Check if the 'traci' library is installed
try:
    import traci
    print(f"[SUCCESS] Traci (the bridge to SUMO) is installed.")
except ImportError:
    print("[FAIL] Traci is missing. Run 'pip install traci'")

# 3. Check if the SUMO program actually runs
if shutil.which('sumo'):
    print(f"[SUCCESS] The SUMO app is reachable.")
else:
    print("[WARNING] 'sumo' command not found. You might need to add the 'bin' folder to Path, but let's see if the simulation runs first.")

print("\nIf you see SUCCESS above, we are ready for Phase 2!")