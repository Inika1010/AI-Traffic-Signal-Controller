import os
import sys
import subprocess
import gzip
import shutil

# 1. Setup SUMO Tools
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    randomTripsPath = os.path.join(tools, 'randomTrips.py')
else:
    sys.exit("Error: SUMO_HOME is not set.")

print("--- GENERATING HEAVY TRAFFIC (MANUAL DECOMPRESS) ---")

# 2. LOCATE THE FILE
gz_file = "osm.net.xml.gz"
temp_xml_file = "temp_network.net.xml" # We will create this
output_file = "osm.passenger.trips.xml"

if not os.path.exists(gz_file):
    sys.exit(f"Error: Could not find {gz_file}")

# 3. MANUALLY DECOMPRESS (The Fix)
print(f"-> Unzipping {gz_file} to {temp_xml_file}...")
try:
    with gzip.open(gz_file, 'rb') as f_in:
        with open(temp_xml_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
except Exception as e:
    sys.exit(f"Error unzipping file: {e}")

# 4. RUN GENERATOR ON THE CLEAN XML
# Now we pass the plain .xml file, so no "invalid token" errors possible.
cmd = [
    sys.executable, randomTripsPath,
    "-n", temp_xml_file,   # Use the clean unzipped file
    "-r", output_file,
    "-e", "3600",
    "-p", "4.0",           # Heavy traffic
    "--validate"
]

print("-> Running Traffic Generator...")
try:
    subprocess.run(cmd, check=True)
    print("\n--- SUCCESS: Heavy traffic file created! ---")
except subprocess.CalledProcessError as e:
    print(f"\n[FAIL] Generator crashed. Error code: {e.returncode}")
finally:
    # 5. CLEAN UP
    if os.path.exists(temp_xml_file):
        os.remove(temp_xml_file)
        print("-> Temporary file cleaned up.")