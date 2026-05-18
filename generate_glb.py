import trimesh
import numpy as np
import math

# Create base
base = trimesh.creation.cylinder(radius=1.2, height=0.2, sections=64)
base.visual.face_colors = [160, 160, 170, 255]

# Create sloped part (cone frustum)
sloped = trimesh.creation.cylinder(radius=1.2, height=0.6, sections=64)
# Scale top vertices
for i, v in enumerate(sloped.vertices):
    if v[2] > 0: # top vertices
        sloped.vertices[i][0] *= (0.7 / 1.2)
        sloped.vertices[i][1] *= (0.7 / 1.2)
sloped.apply_translation([0, 0, 0.4]) # translate up
sloped.visual.face_colors = [180, 180, 190, 255]

# Top flat part
top = trimesh.creation.cylinder(radius=0.7, height=0.1, sections=64)
top.apply_translation([0, 0, 0.75])
top.visual.face_colors = [150, 150, 160, 255]

# Hub
hub = trimesh.creation.cylinder(radius=0.15, height=0.2, sections=32)
hub.apply_translation([0, 0, 0.9])
hub.visual.face_colors = [60, 60, 60, 255]

nut = trimesh.creation.cylinder(radius=0.08, height=0.1, sections=16)
nut.apply_translation([0, 0, 1.05])
nut.visual.face_colors = [210, 210, 210, 255]

parts = [base, sloped, top, hub, nut]

# Tubes
num_tubes = 12
tube_radius = 0.12
tube_height = 0.5
tilt = math.radians(40)

for i in range(num_tubes):
    angle = 2.0 * math.pi * i / num_tubes
    
    tube = trimesh.creation.cylinder(radius=tube_radius, height=tube_height, sections=16)
    tube.visual.face_colors = [40, 120, 220, 255] # Blue
    
    cap = trimesh.creation.cylinder(radius=tube_radius*1.1, height=0.05, sections=16)
    cap.apply_translation([0, 0, tube_height/2 + 0.025])
    cap.visual.face_colors = [220, 40, 40, 255] # Red
    
    # Combine tube and cap into a single mesh
    tube_assembly = trimesh.util.concatenate([tube, cap])
    
    # Rotate tilt around X axis
    mat_tilt = trimesh.transformations.rotation_matrix(tilt, [1, 0, 0])
    tube_assembly.apply_transform(mat_tilt)
    
    # Rotate around Z axis (distribute)
    mat_z = trimesh.transformations.rotation_matrix(angle, [0, 0, 1])
    tube_assembly.apply_transform(mat_z)
    
    # Translate to position
    r_pos = 0.85
    z_pos = 0.5
    tube_assembly.apply_translation([r_pos * math.cos(angle), r_pos * math.sin(angle), z_pos])
    
    parts.append(tube_assembly)

# Combine all into a single scene
scene = trimesh.Scene(parts)

# Rotate so Y is up (trimesh default is Z up)
mat_y_up = trimesh.transformations.rotation_matrix(-math.pi/2, [1, 0, 0])
for geom in scene.geometry.values():
    geom.apply_transform(mat_y_up)

# Export
scene.export("/mnt/36270add-d8d7-4990-b2b6-c9c5f803b31b/Hackatones/Transforming Enterprise Through AI/Repo/assets/centrifuge_v3.glb")
print("GLB generated successfully.")
