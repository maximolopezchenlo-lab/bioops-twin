import math
import os

def create_centrifuge_model():
    assets_dir = "assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    obj_path = os.path.join(assets_dir, "centrifuge_rotor_new.obj")
    mtl_path = os.path.join(assets_dir, "centrifuge_rotor_new.mtl")
    
    # Create Material file
    with open(mtl_path, "w") as f:
        f.write("# Material for BioOps Centrifuge\n")
        f.write("newmtl MetalRotor\n")
        f.write("Ka 0.2 0.2 0.2\n") # Ambient
        f.write("Kd 0.7 0.7 0.8\n") # Diffuse (greyish blue metal)
        f.write("Ks 0.9 0.9 0.9\n") # Specular
        f.write("Ns 100.0\n") # Shininess
        f.write("d 1.0\n") # Opaqueness
        f.write("illum 2\n")
        
        f.write("\nnewmtl RedTube\n")
        f.write("Ka 0.2 0.0 0.0\n")
        f.write("Kd 0.8 0.1 0.1\n")
        f.write("Ks 0.5 0.5 0.5\n")
        f.write("Ns 50.0\n")
        f.write("d 1.0\n")
        f.write("illum 2\n")
    
    # Create OBJ file
    with open(obj_path, "w") as f:
        f.write("mtllib centrifuge_rotor_new.mtl\n")
        
        # We will build a central cylinder and a few smaller cylinders for tubes
        vertices = []
        faces = []
        
        def add_cylinder(r, h, offset_x=0, offset_y=0, offset_z=0, segments=32, material="MetalRotor"):
            start_v = len(vertices) + 1
            # Vertices
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = r * math.cos(angle) + offset_x
                z = r * math.sin(angle) + offset_z
                vertices.append((x, offset_y + h, z))
                vertices.append((x, offset_y, z))
            # Center top and bottom
            vertices.append((offset_x, offset_y + h, offset_z))
            top_center = len(vertices)
            vertices.append((offset_x, offset_y, offset_z))
            bottom_center = len(vertices)
            
            f.write(f"usemtl {material}\n")
            
            # Faces
            for i in range(segments):
                next_i = (i + 1) % segments
                t1 = start_v + i * 2
                b1 = start_v + i * 2 + 1
                t2 = start_v + next_i * 2
                b2 = start_v + next_i * 2 + 1
                
                # Side
                faces.append((t1, b1, b2))
                faces.append((t1, b2, t2))
                
                # Top
                faces.append((top_center, t2, t1))
                # Bottom
                faces.append((bottom_center, b1, b2))
        
        # Add main rotor
        add_cylinder(r=1.5, h=0.5, offset_y=-0.25, segments=32, material="MetalRotor")
        # Add central hub
        add_cylinder(r=0.3, h=0.8, offset_y=-0.25, segments=16, material="MetalRotor")
        
        # Add 6 tubes
        for i in range(6):
            angle = 2 * math.pi * i / 6
            x = 1.0 * math.cos(angle)
            z = 1.0 * math.sin(angle)
            add_cylinder(r=0.15, h=0.6, offset_x=x, offset_y=0, offset_z=z, segments=12, material="RedTube")
            
        # Write vertices
        for v in vertices:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            
        # Write faces
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")
            
    print(f"Created {obj_path} and {mtl_path}")

create_centrifuge_model()
