import math
import os

filepath = "/mnt/36270add-d8d7-4990-b2b6-c9c5f803b31b/Hackatones/Transforming Enterprise Through AI/Repo/assets/centrifuge.obj"

segments = 32
radius = 1.0
height = 0.5

with open(filepath, "w") as f:
    f.write("# Centrifuge Rotor (Cylinder)\n")
    f.write("o Centrifuge\n")
    
    # Vertices
    # Top center
    f.write(f"v 0.0 {height/2} 0.0\n")
    # Bottom center
    f.write(f"v 0.0 {-height/2} 0.0\n")
    
    # Top circle
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        f.write(f"v {x} {height/2} {z}\n")
        
    # Bottom circle
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        x = radius * math.cos(theta)
        z = radius * math.sin(theta)
        f.write(f"v {x} {-height/2} {z}\n")
        
    # Faces
    # Top face
    top_center_idx = 1
    bottom_center_idx = 2
    top_start = 3
    bottom_start = 3 + segments
    
    for i in range(segments):
        n1 = i
        n2 = (i + 1) % segments
        # top triangle
        f.write(f"f {top_center_idx} {top_start + n1} {top_start + n2}\n")
        
    # Bottom face (reverse winding)
    for i in range(segments):
        n1 = i
        n2 = (i + 1) % segments
        f.write(f"f {bottom_center_idx} {bottom_start + n2} {bottom_start + n1}\n")
        
    # Sides
    for i in range(segments):
        n1 = i
        n2 = (i + 1) % segments
        
        t1 = top_start + n1
        t2 = top_start + n2
        b1 = bottom_start + n1
        b2 = bottom_start + n2
        
        # quad
        f.write(f"f {t1} {b1} {b2} {t2}\n")

print("Generated centrifuge.obj")
