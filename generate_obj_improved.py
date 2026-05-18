import math
import os

filepath = "/mnt/36270add-d8d7-4990-b2b6-c9c5f803b31b/Hackatones/Transforming Enterprise Through AI/Repo/assets/centrifuge_v2.obj"
mtlpath = "/mnt/36270add-d8d7-4990-b2b6-c9c5f803b31b/Hackatones/Transforming Enterprise Through AI/Repo/assets/centrifuge_v2.mtl"

with open(mtlpath, 'w') as f:
    f.write("""newmtl RotorBody
Kd 0.75 0.75 0.78
Ks 0.3 0.3 0.3
Ns 30

newmtl RotorHub
Kd 0.25 0.25 0.25
Ks 0.8 0.8 0.8
Ns 100

newmtl Tube
Kd 0.15 0.45 0.85
Ks 0.9 0.9 0.9
Ns 80

newmtl TubeCap
Kd 0.9 0.1 0.1
Ks 0.5 0.5 0.5
Ns 50
""")

vertices = []
faces_and_mtls = []

def add_vertex(x, y, z):
    vertices.append((x, y, z))
    return len(vertices)

def add_face(v_indices):
    faces_and_mtls.append(v_indices)

def set_material(name):
    faces_and_mtls.append(f"usemtl {name}")

def multiply_matrix_vector(matrix, vector):
    return [
        matrix[0][0]*vector[0] + matrix[0][1]*vector[1] + matrix[0][2]*vector[2],
        matrix[1][0]*vector[0] + matrix[1][1]*vector[1] + matrix[1][2]*vector[2],
        matrix[2][0]*vector[0] + matrix[2][1]*vector[1] + matrix[2][2]*vector[2]
    ]

def create_rotated_cylinder(cx, cy, cz, r_bottom, r_top, h, angle_y, angle_tilt, segments=24):
    mat_tilt = [
        [1, 0, 0],
        [0, math.cos(angle_tilt), -math.sin(angle_tilt)],
        [0, math.sin(angle_tilt), math.cos(angle_tilt)]
    ]
    
    mat_y = [
        [math.cos(angle_y), 0, math.sin(angle_y)],
        [0, 1, 0],
        [-math.sin(angle_y), 0, math.cos(angle_y)]
    ]
    
    def transform(x, y, z):
        v = [x, y, z]
        v = multiply_matrix_vector(mat_tilt, v)
        v = multiply_matrix_vector(mat_y, v)
        return (v[0]+cx, v[1]+cy, v[2]+cz)

    bc = add_vertex(*transform(0, 0, 0))
    tc = add_vertex(*transform(0, h, 0))
    
    base_indices = []
    top_indices = []
    
    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        lx = r_bottom * math.cos(theta)
        lz = r_bottom * math.sin(theta)
        base_indices.append(add_vertex(*transform(lx, 0, lz)))
        
        tx = r_top * math.cos(theta)
        tz = r_top * math.sin(theta)
        top_indices.append(add_vertex(*transform(tx, h, tz)))
        
    for i in range(segments):
        n1 = i
        n2 = (i+1)%segments
        add_face([bc, base_indices[n2], base_indices[n1]])
        
    for i in range(segments):
        n1 = i
        n2 = (i+1)%segments
        add_face([tc, top_indices[n1], top_indices[n2]])
        
    for i in range(segments):
        n1 = i
        n2 = (i+1)%segments
        add_face([base_indices[n1], base_indices[n2], top_indices[n2], top_indices[n1]])

def create_cylinder(x, y, z, r_bottom, r_top, h, segments=48):
    create_rotated_cylinder(x, y, z, r_bottom, r_top, h, 0, 0, segments)

# Build the geometry
set_material("RotorBody")
# Base flat cylinder
create_cylinder(0, 0, 0, 1.2, 1.2, 0.15, 64)
# Main conical body
create_cylinder(0, 0.15, 0, 1.2, 0.7, 0.6, 64)
# Top flat part
create_cylinder(0, 0.75, 0, 0.7, 0.6, 0.1, 64)

set_material("RotorHub")
# Hub spindle
create_cylinder(0, 0.85, 0, 0.15, 0.15, 0.15, 32)
# Spindle nut
create_cylinder(0, 1.0, 0, 0.08, 0.08, 0.08, 16)

# Create tubes (angled)
num_tubes = 12
tube_radius = 0.14
tube_height = 0.4
tilt = math.radians(40) # 40 degrees tilt

for i in range(num_tubes):
    angle_y = 2.0 * math.pi * i / num_tubes
    
    # Position: shift outwards and upwards
    # We want the tubes to be embedded in the sloped face.
    # The sloped face goes from r=1.2 at y=0.15 to r=0.7 at y=0.75.
    # Let's put the center of the tube cap at r=0.8, y=0.65
    r_pos = 0.85
    y_pos = 0.6
    
    cx = r_pos * math.cos(angle_y)
    cz = -r_pos * math.sin(angle_y) # negative to match rotation direction if needed
    
    set_material("Tube")
    # Actually the tube goes INWARDS. So the cylinder should start at cap and go down?
    # Our cylinder starts at (cx, cy, cz) and goes UP locally.
    # If we want it to go down, we can start low and go up to cap.
    # Let's start the tube deep inside and go up to the cap surface.
    # To do this, we'll start at cx, cy, cz and go UP by tube_height.
    # Wait, the tilt is around X axis. Positive tilt tilts +Y towards +Z.
    # Let's just adjust the start position so it protrudes perfectly.
    
    start_r = 0.5
    start_y = 0.3
    sx = start_r * math.cos(angle_y)
    sz = start_r * math.sin(angle_y)
    
    create_rotated_cylinder(sx, start_y, sz, tube_radius, tube_radius, tube_height, -angle_y, tilt, 16)
    
    # Add a tube cap
    set_material("TubeCap")
    # Cap is at local top.
    # We can just create another small cylinder at the top of the tube.
    # The local Y of the top is tube_height. We can just shift our start position locally.
    # Local shift: 
    # v = [0, tube_height, 0]
    # transformed:
    mat_tilt = [
        [1, 0, 0],
        [0, math.cos(tilt), -math.sin(tilt)],
        [0, math.sin(tilt), math.cos(tilt)]
    ]
    mat_y = [
        [math.cos(-angle_y), 0, math.sin(-angle_y)],
        [0, 1, 0],
        [-math.sin(-angle_y), 0, math.cos(-angle_y)]
    ]
    v = multiply_matrix_vector(mat_tilt, [0, tube_height, 0])
    v = multiply_matrix_vector(mat_y, v)
    cap_x = sx + v[0]
    cap_y = start_y + v[1]
    cap_z = sz + v[2]
    
    create_rotated_cylinder(cap_x, cap_y, cap_z, tube_radius*1.1, tube_radius*1.1, 0.05, -angle_y, tilt, 16)

with open(filepath, 'w') as f:
    f.write(f"mtllib centrifuge_v2.mtl\n")
    f.write("o CentrifugeRotor\n")
    for v in vertices:
        f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
    for item in faces_and_mtls:
        if isinstance(item, str):
            f.write(item + "\n")
        else:
            f.write("f " + " ".join(str(idx) for idx in item) + "\n")

print("Detailed 3D model generated.")
