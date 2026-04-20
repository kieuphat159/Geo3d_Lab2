import json
import os
from pathlib import Path

def parse_obj_file(obj_file_path):
    """Parse OBJ file and return a structured dictionary"""
    data = {
        "vertices": [],
        "textures": [],
        "normals": [],
        "faces": [],
        "groups": [],
        "materials": [],
        "material_props": {},
        "metadata": {
            "file": os.path.basename(obj_file_path)
        }
    }
    
    current_group = None
    current_material = None
    
    with open(obj_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            cmd = parts[0]
            
            # Vertices (v)
            if cmd == 'v':
                data["vertices"].append({
                    "index": len(data["vertices"]),
                    "x": float(parts[1]),
                    "y": float(parts[2]),
                    "z": float(parts[3])
                })
            
            # Texture coordinates (vt)
            elif cmd == 'vt':
                data["textures"].append({
                    "index": len(data["textures"]),
                    "u": float(parts[1]),
                    "v": float(parts[2]) if len(parts) > 2 else 0
                })
            
            # Normals (vn)
            elif cmd == 'vn':
                data["normals"].append({
                    "index": len(data["normals"]),
                    "x": float(parts[1]),
                    "y": float(parts[2]),
                    "z": float(parts[3])
                })
            
            # Faces (f)
            elif cmd == 'f':
                face = {
                    "vertices": [],
                    "textures": [],
                    "normals": [],
                    "material": current_material,
                    "group": current_group
                }
                
                for i in range(1, len(parts)):
                    vertex_data = parts[i].split('/')
                    
                    if len(vertex_data) >= 1 and vertex_data[0]:
                        face["vertices"].append(int(vertex_data[0]) - 1)  # OBJ indices are 1-based
                    
                    if len(vertex_data) >= 2 and vertex_data[1]:
                        face["textures"].append(int(vertex_data[1]) - 1)
                    
                    if len(vertex_data) >= 3 and vertex_data[2]:
                        face["normals"].append(int(vertex_data[2]) - 1)
                
                data["faces"].append(face)
            
            # Groups (g)
            elif cmd == 'g':
                current_group = ' '.join(parts[1:])
                if current_group not in data["groups"]:
                    data["groups"].append(current_group)
            
            # Materials (usemtl)
            elif cmd == 'usemtl':
                current_material = ' '.join(parts[1:])
                if current_material not in data["materials"]:
                    data["materials"].append(current_material)
            
            # Material library (mtllib)
            elif cmd == 'mtllib':
                # record material library filename(s)
                libs = parts[1:]
                data["metadata"]["material_library"] = ' '.join(libs)

                # attempt to parse referenced .mtl files (relative to obj file)
                obj_dir = os.path.dirname(obj_file_path)
                for lib in libs:
                    lib_path = lib
                    if not os.path.isabs(lib_path):
                        lib_path = os.path.join(obj_dir, lib)
                    if os.path.exists(lib_path):
                        current_mtl = None
                        with open(lib_path, 'r', encoding='utf-8', errors='ignore') as mtlf:
                            for mline in mtlf:
                                mline = mline.strip()
                                if not mline or mline.startswith('#'):
                                    continue
                                mparts = mline.split()
                                if not mparts:
                                    continue
                                mcmd = mparts[0]
                                if mcmd == 'newmtl':
                                    current_mtl = ' '.join(mparts[1:])
                                    data['material_props'][current_mtl] = {}
                                elif mcmd == 'Kd' and current_mtl:
                                    # diffuse color
                                    try:
                                        r = float(mparts[1])
                                        g = float(mparts[2])
                                        b = float(mparts[3])
                                        data['material_props'][current_mtl]['Kd'] = [r, g, b]
                                    except Exception:
                                        pass
                                elif mcmd == 'Ka' and current_mtl:
                                    try:
                                        r = float(mparts[1])
                                        g = float(mparts[2])
                                        b = float(mparts[3])
                                        data['material_props'][current_mtl]['Ka'] = [r, g, b]
                                    except Exception:
                                        pass
                                elif mcmd == 'Ks' and current_mtl:
                                    try:
                                        r = float(mparts[1])
                                        g = float(mparts[2])
                                        b = float(mparts[3])
                                        data['material_props'][current_mtl]['Ks'] = [r, g, b]
                                    except Exception:
                                        pass
                                elif mcmd == 'map_Kd' and current_mtl:
                                    # texture map for diffuse
                                    data['material_props'][current_mtl]['map_Kd'] = ' '.join(mparts[1:])
    
    return data

def convert_obj_to_json(obj_file_path, output_json_path):
    """Convert OBJ file to JSON and save"""
    print(f"Converting: {obj_file_path}")
    data = parse_obj_file(obj_file_path)
    
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {output_json_path}")
    print(f"  - Vertices: {len(data['vertices'])}")
    print(f"  - Faces: {len(data['faces'])}")
    print(f"  - Groups: {len(data['groups'])}")
    print(f"  - Materials: {len(data['materials'])}")
    print()

# Auto-discover .obj files under the script directory and convert them
base_dir = os.path.dirname(os.path.abspath(__file__))
found = []
for root, dirs, files in os.walk(base_dir):
    for fn in files:
        if fn.lower().endswith('.obj'):
            found.append(os.path.join(root, fn))

if not found:
    print("No .obj files found under:", base_dir)
else:
    for obj_file in found:
        base_name = Path(obj_file).stem
        json_output = os.path.join(base_dir, f"{base_name}.json")
        convert_obj_to_json(obj_file, json_output)

print("Conversion complete!")
