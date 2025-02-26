import matplotlib.pyplot as plt
import networkx as nx
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def generate_monolithic_architecture():
    """Generate visualization of current monolithic architecture"""
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes - Components of the monolithic architecture
    G.add_node("Frontend UI", pos=(0, 4), node_color="lightblue")
    G.add_node("Business Logic", pos=(0, 2), node_color="lightgreen")
    G.add_node("Database", pos=(0, 0), node_color="lightcoral")
    
    # Add supporting components
    G.add_node("Authentication", pos=(-2, 3), node_color="wheat")
    G.add_node("Logging", pos=(-2, 1), node_color="wheat")
    G.add_node("Error Handling", pos=(2, 3), node_color="pink")
    G.add_node("Analytics", pos=(2, 1), node_color="pink")
    
    # Add edges to show relationships and dependencies
    edges = [
        ("Frontend UI", "Business Logic"),
        ("Business Logic", "Database"),
        ("Frontend UI", "Authentication"),
        ("Business Logic", "Authentication"),
        ("Business Logic", "Logging"),
        ("Frontend UI", "Error Handling"),
        ("Business Logic", "Error Handling"),
        ("Database", "Analytics"),
        ("Business Logic", "Analytics")
    ]
    G.add_edges_from(edges)
    
    # Create the figure and draw the graph
    plt.figure(figsize=(12, 8))
    pos = nx.get_node_attributes(G, 'pos')
    
    # Draw nodes with different colors based on component type
    node_colors = [data.get("node_color", "lightgray") for _, data in G.nodes(data=True)]
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color=node_colors, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.5, arrowsize=20, alpha=0.7, 
                           edge_color="gray", arrows=True)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')
    
    # Add title and annotations
    plt.title("Current Monolithic Architecture - Customer Engagement System", fontsize=16, pad=20)
    plt.text(0, -1.5, "Key Issues:\n• Heavy coupling between components\n• Inconsistent error handling\n• Scaling challenges", 
             ha='center', bbox=dict(facecolor='lightyellow', alpha=0.5, boxstyle='round,pad=0.5'))
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("monolithic_architecture.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Monolithic architecture diagram generated: monolithic_architecture.png")

def generate_microservices_architecture():
    """Generate visualization of proposed microservices architecture"""
    # Create figure
    plt.figure(figsize=(15, 10))
    
    # Service positions
    services = {
        "API Gateway": (5, 8),
        "User Auth Service": (2, 6),
        "Customer Profile Service": (5, 6),
        "Analytics Service": (8, 6),
        "Engagement Service": (2, 4),
        "Notification Service": (5, 4),
        "Reporting Service": (8, 4),
        "Data Access Layer": (5, 2),
        "Customer DB": (3, 0),
        "Analytics DB": (7, 0),
    }
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for service, pos in services.items():
        if "DB" in service:
            node_color = "lightcoral"
        elif "Service" in service:
            node_color = "lightgreen"
        elif "Gateway" in service:
            node_color = "lightskyblue"
        elif "Layer" in service:
            node_color = "wheat"
        else:
            node_color = "lightgray"
        
        G.add_node(service, pos=pos, node_color=node_color)
    
    # Add edges
    edges = [
        ("API Gateway", "User Auth Service"),
        ("API Gateway", "Customer Profile Service"),
        ("API Gateway", "Analytics Service"),
        ("API Gateway", "Engagement Service"),
        ("API Gateway", "Notification Service"),
        ("API Gateway", "Reporting Service"),
        ("User Auth Service", "Data Access Layer"),
        ("Customer Profile Service", "Data Access Layer"),
        ("Analytics Service", "Data Access Layer"),
        ("Engagement Service", "Data Access Layer"),
        ("Notification Service", "Data Access Layer"),
        ("Reporting Service", "Data Access Layer"),
        ("Data Access Layer", "Customer DB"),
        ("Data Access Layer", "Analytics DB"),
        ("Analytics Service", "Reporting Service"),
        ("Engagement Service", "Notification Service"),
    ]
    G.add_edges_from(edges)
    
    # Draw the graph
    pos = nx.get_node_attributes(G, 'pos')
    
    # Draw nodes with different colors based on component type
    node_colors = [data.get("node_color", "lightgray") for _, data in G.nodes(data=True)]
    nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=node_colors, alpha=0.8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.5, arrowsize=15, alpha=0.7, 
                          edge_color="gray", arrows=True)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    # Add title and annotations
    plt.title("Proposed Microservices Architecture - Customer Engagement System", fontsize=16, pad=20)
    
    plt.text(5, -1.5, "Benefits:\n• Improved scalability\n• Easier maintenance\n• Independent deployment\n• Improved fault isolation", 
             ha='center', bbox=dict(facecolor='lightyellow', alpha=0.5, boxstyle='round,pad=0.5'))
    
    # Implementation phases
    phases = {
        "Phase 1 (0-3 months)": "Database query optimization & error handling standardization",
        "Phase 2 (3-6 months)": "Begin with Analytics & Reporting services",
        "Phase 3 (6+ months)": "Complete migration to microservices architecture"
    }
    
    y_pos = 9.5
    for phase, description in phases.items():
        plt.text(1, y_pos, f"{phase}: {description}", fontsize=9,
                bbox=dict(facecolor='lavender', alpha=0.5, boxstyle='round,pad=0.3'))
        y_pos -= 0.7
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("microservices_architecture.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Microservices architecture diagram generated: microservices_architecture.png")

def create_comparison_image():
    """Create a side-by-side comparison of current vs proposed architecture"""
    # Open the two images
    try:
        current = Image.open("monolithic_architecture.png")
        proposed = Image.open("microservices_architecture.png")
        
        # Create a new image with both diagrams side by side
        total_width = current.width + proposed.width
        max_height = max(current.height, proposed.height)
        
        comparison = Image.new('RGB', (total_width, max_height + 100), color='white')
        
        # Paste the images
        comparison.paste(current, (0, 50))
        comparison.paste(proposed, (current.width, 50))
        
        # Add header text
        draw = ImageDraw.Draw(comparison)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            # Fallback to default font if arial is not available
            font = ImageFont.load_default()
        
        draw.text((total_width//2, 20), "Architecture Transformation", fill="black", font=font, anchor="mm")
        draw.text((current.width//2, 50), "Current State", fill="black", font=font, anchor="mm")
        draw.text((current.width + proposed.width//2, 50), "Future State", fill="black", font=font, anchor="mm")
        
        # Save the comparison image
        comparison.save("architecture_comparison.png")
        print("Comparison image generated: architecture_comparison.png")
    except Exception as e:
        print(f"Error creating comparison image: {e}")

def main():
    """Generate all architecture diagrams"""
    print("Generating Customer Engagement System Architecture Diagrams...")
    generate_monolithic_architecture()
    generate_microservices_architecture()
    create_comparison_image()
    print("Done! All diagrams have been generated.")

if __name__ == "__main__":
    main()