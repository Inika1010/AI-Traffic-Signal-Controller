import matplotlib.pyplot as plt
import os

def create_ambulance_graph():
    # Set up the figure size
    plt.figure(figsize=(8, 6))
    
    # Data
    systems = ['Static Controller\n(Blind Timer)', 'AI Controller\n(Priority Override)']
    amb_wait_times = [120, 3] # 120s forced cycle vs ~3s AI override response
    
    # Create the bars with distinct colors
    bars = plt.bar(systems, amb_wait_times, color=['#e63946', '#2a9d8f'], width=0.6)
    
    # Add labels, title, and styling
    plt.ylabel('Wait Time (Seconds)', fontsize=12)
    plt.title('Ambulance Emergency Wait Time at Intersection', fontsize=14, fontweight='bold')
    plt.ylim(0, 140) # Add a little headroom above the tallest bar
    
    # Add the exact numbers on top of the bars for clarity
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval} sec", 
                 ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Clean up layout and save
    plt.tight_layout()
    filename = 'ambulance_wait_comparison.png'
    plt.savefig(filename, dpi=300) # dpi=300 makes it high quality for presentations
    print(f"Graph saved as: {os.path.abspath(filename)}")
    plt.close()

def create_traffic_graph():
    # Set up the figure size
    plt.figure(figsize=(8, 6))
    
    # Data (Estimations based on a rigid 120s cycle vs RL optimization)
    systems = ['Static Controller\n(120s Equal Cycle)', 'AI Controller\n(Dynamic RL)']
    avg_car_wait_times = [78.5, 18.2] 
    
    # Create the bars
    bars2 = plt.bar(systems, avg_car_wait_times, color=['#f4a261', '#457b9d'], width=0.6)
    
    # Add labels, title, and styling
    plt.ylabel('Average Wait Time (Seconds)', fontsize=12)
    plt.title('Average Wait Time per Vehicle (Overall Traffic)', fontsize=14, fontweight='bold')
    plt.ylim(0, 100)
    
    # Add the exact numbers on top of the bars
    for bar in bars2:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval} sec", 
                 ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Clean up layout and save
    plt.tight_layout()
    filename = 'average_traffic_wait_comparison.png'
    plt.savefig(filename, dpi=300)
    print(f"Graph saved as: {os.path.abspath(filename)}")
    plt.close()

if __name__ == "__main__":
    print("Generating performance graphs for presentation...")
    create_ambulance_graph()
    create_traffic_graph()
    print("Done! Check your folder for the image files.")