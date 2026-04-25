import base64
import json
import os
import struct
from pathlib import Path


GLTF_COMPONENT_TYPES = {
    5120: "b",
    5121: "B",
    5122: "h",
    5123: "H",
    5125: "I",
    5126: "f",
}

GLTF_TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16,
}


def identity_matrix():
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def matrix_multiply(left, right):
    result = [[0.0] * 4 for _ in range(4)]
    for row in range(4):
        for col in range(4):
            result[row][col] = sum(left[row][k] * right[k][col] for k in range(4))
    return result


def translation_matrix(translation):
    tx, ty, tz = translation
    return [
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, tz],
        [0.0, 0.0, 0.0, 1.0],
    ]


def scale_matrix(scale):
    sx, sy, sz = scale
    return [
        [sx, 0.0, 0.0, 0.0],
        [0.0, sy, 0.0, 0.0],
        [0.0, 0.0, sz, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def rotation_matrix_from_quaternion(rotation):
    x, y, z, w = rotation
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z

    return [
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy), 0.0],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx), 0.0],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def transform_point(matrix, point):
    x, y, z = point
    return [
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + matrix[0][3],
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + matrix[1][3],
        matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + matrix[2][3],
    ]


def node_local_matrix(node):
    if "matrix" in node:
        values = node["matrix"]
        return [
            [values[0], values[4], values[8], values[12]],
            [values[1], values[5], values[9], values[13]],
            [values[2], values[6], values[10], values[14]],
            [values[3], values[7], values[11], values[15]],
        ]

    local = identity_matrix()

    if "translation" in node:
        local = matrix_multiply(local, translation_matrix(node["translation"]))
    if "rotation" in node:
        local = matrix_multiply(local, rotation_matrix_from_quaternion(node["rotation"]))
    if "scale" in node:
        local = matrix_multiply(local, scale_matrix(node["scale"]))

    return local


def load_resource_bytes(resource_path, base_dir):
    if resource_path.startswith("data:"):
        _, encoded = resource_path.split(",", 1)
        return base64.b64decode(encoded)

    resolved_path = resource_path
    if not os.path.isabs(resolved_path):
        resolved_path = os.path.join(base_dir, resource_path)

    with open(resolved_path, "rb") as file_handle:
        return file_handle.read()


def decode_accessor(gltf, accessor_index, buffers):
    accessor = gltf["accessors"][accessor_index]
    buffer_view = gltf["bufferViews"][accessor["bufferView"]]

    component_format = GLTF_COMPONENT_TYPES[accessor["componentType"]]
    component_count = GLTF_TYPE_COMPONENTS[accessor["type"]]

    buffer_data = buffers[buffer_view["buffer"]]
    start = buffer_view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = buffer_view.get("byteStride", struct.calcsize("<" + component_format) * component_count)

    values = []
    for index in range(accessor["count"]):
        offset = start + index * stride
        unpacked = struct.unpack_from("<" + component_format * component_count, buffer_data, offset)
        if component_count == 1:
            values.append(unpacked[0])
        else:
            values.append(list(unpacked))

    return values


def extract_texture_path(gltf, texture_index, gltf_path, output_json_path):
    textures = gltf.get("textures", [])
    images = gltf.get("images", [])

    if texture_index is None or texture_index >= len(textures):
        return None

    texture = textures[texture_index]
    image_index = texture.get("source")
    if image_index is None or image_index >= len(images):
        return None

    image = images[image_index]
    uri = image.get("uri")
    if not uri:
        return None

    if uri.startswith("data:"):
        return uri

    gltf_dir = os.path.dirname(gltf_path)
    image_path = os.path.normpath(os.path.join(gltf_dir, uri))
    return os.path.relpath(image_path, os.path.dirname(output_json_path))


def parse_gltf_file(gltf_path, output_json_path=None):
    with open(gltf_path, "r", encoding="utf-8") as file_handle:
        gltf = json.load(file_handle)

    base_dir = os.path.dirname(gltf_path)
    if output_json_path is None:
        output_json_path = os.path.join(base_dir, f"{Path(gltf_path).stem}.json")

    buffers = []
    for buffer_info in gltf.get("buffers", []):
        buffers.append(load_resource_bytes(buffer_info["uri"], base_dir))

    data = {
        "vertices": [],
        "textures": [],
        "normals": [],
        "faces": [],
        "groups": [],
        "materials": [],
        "material_props": {},
        "metadata": {
            "file": os.path.basename(gltf_path),
            "source": "gltf",
            "generator": gltf.get("asset", {}).get("generator"),
        },
    }

    def add_material(material_index):
        if material_index is None or material_index >= len(gltf.get("materials", [])):
            material_name = "default"
            material_props = {}
        else:
            material = gltf["materials"][material_index]
            material_name = material.get("name") or f"material_{material_index}"
            pbr = material.get("pbrMetallicRoughness", {})
            base_color = pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])
            material_props = {
                "Kd": [float(base_color[0]), float(base_color[1]), float(base_color[2])],
                "metallicFactor": pbr.get("metallicFactor", 0.0),
                "roughnessFactor": pbr.get("roughnessFactor", 1.0),
            }
            texture_info = pbr.get("baseColorTexture")
            if texture_info:
                texture_path = extract_texture_path(
                    gltf,
                    texture_info.get("index"),
                    gltf_path,
                    output_json_path,
                )
                if texture_path:
                    material_props["map_Kd"] = texture_path
                    material_props["map_Kd_flipY"] = False
            if material.get("doubleSided"):
                material_props["doubleSided"] = True

        if material_name not in data["materials"]:
            data["materials"].append(material_name)
        if material_name not in data["material_props"]:
            data["material_props"][material_name] = material_props

        return material_name

    def traverse_scene(node_index, parent_matrix):
        node = gltf["nodes"][node_index]
        local_matrix = node_local_matrix(node)
        world_matrix = matrix_multiply(parent_matrix, local_matrix)

        mesh_index = node.get("mesh")
        if mesh_index is not None:
            mesh = gltf["meshes"][mesh_index]
            group_name = node.get("name") or mesh.get("name") or f"mesh_{mesh_index}"

            for primitive in mesh.get("primitives", []):
                if primitive.get("mode", 4) != 4:
                    continue

                material_name = add_material(primitive.get("material"))

                position_accessor = primitive["attributes"]["POSITION"]
                positions = decode_accessor(gltf, position_accessor, buffers)
                texcoord_accessor = primitive["attributes"].get("TEXCOORD_0")
                texcoords = decode_accessor(gltf, texcoord_accessor, buffers) if texcoord_accessor is not None else []
                index_accessor = primitive.get("indices")
                indices = decode_accessor(gltf, index_accessor, buffers) if index_accessor is not None else list(range(len(positions)))

                vertex_offset = len(data["vertices"])
                texture_offset = len(data["textures"])

                for position in positions:
                    transformed = transform_point(world_matrix, position)
                    data["vertices"].append(
                        {
                            "index": len(data["vertices"]),
                            "x": transformed[0],
                            "y": transformed[1],
                            "z": transformed[2],
                        }
                    )

                if texcoords:
                    for texcoord in texcoords:
                        data["textures"].append(
                            {
                                "index": len(data["textures"]),
                                "u": float(texcoord[0]),
                                "v": float(texcoord[1]) if len(texcoord) > 1 else 0.0,
                            }
                        )

                for triangle_index in range(0, len(indices), 3):
                    triangle = indices[triangle_index : triangle_index + 3]
                    if len(triangle) < 3:
                        continue

                    face = {
                        "vertices": [vertex_offset + int(triangle[0]), vertex_offset + int(triangle[1]), vertex_offset + int(triangle[2])],
                        "textures": [texture_offset + int(triangle[0]), texture_offset + int(triangle[1]), texture_offset + int(triangle[2])] if texcoords else [],
                        "normals": [],
                        "material": material_name,
                        "group": group_name,
                    }
                    data["faces"].append(face)

        for child_index in node.get("children", []):
            traverse_scene(child_index, world_matrix)

    scene_index = gltf.get("scene", 0)
    scenes = gltf.get("scenes", [])
    if scenes and scene_index < len(scenes):
        root_nodes = scenes[scene_index].get("nodes", [])
    else:
        root_nodes = []

    for root_node in root_nodes:
        traverse_scene(root_node, identity_matrix())

    return data

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


def convert_gltf_to_json(gltf_file_path, output_json_path):
    """Convert glTF file to JSON and save"""
    print(f"Converting: {gltf_file_path}")
    data = parse_gltf_file(gltf_file_path, output_json_path)

    with open(output_json_path, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle, indent=2, ensure_ascii=False)

    print(f"✓ Saved to: {output_json_path}")
    print(f"  - Vertices: {len(data['vertices'])}")
    print(f"  - Faces: {len(data['faces'])}")
    print(f"  - Groups: {len(data['groups'])}")
    print(f"  - Materials: {len(data['materials'])}")
    print()

# Auto-discover model files under the script directory and convert them.
# Prefer glTF over OBJ when both exist for the same stem.
base_dir = os.path.dirname(os.path.abspath(__file__))
selected = {}
priority_map = {
    ".gltf": 0,
    ".obj": 1,
}

for root, dirs, files in os.walk(base_dir):
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in priority_map:
            continue

        file_path = os.path.join(root, fn)
        stem = Path(fn).stem
        priority = priority_map[ext]
        current = selected.get(stem)
        if current is None or priority < current[0]:
            selected[stem] = (priority, file_path)

found = [entry[1] for entry in sorted(selected.values(), key=lambda item: item[1])]

if not found:
    print("No .obj files found under:", base_dir)
else:
    for model_file in found:
        base_name = Path(model_file).stem
        json_output = os.path.join(base_dir, f"{base_name}.json")
        if model_file.lower().endswith(".gltf"):
            convert_gltf_to_json(model_file, json_output)
        else:
            convert_obj_to_json(model_file, json_output)

print("Conversion complete!")
