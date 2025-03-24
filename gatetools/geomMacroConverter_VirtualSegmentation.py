import re
import sys
import math
import argparse

def extract_virtual_segmentation(file_path):
    """
    Reads the digitizer file and extracts target pitch values.
    Expects lines with names like "pitchX", "pitchY", or "pitchZ" followed by a number and unit.
    Returns a dictionary mapping axis letters ("X", "Y", "Z") to a value in mm.
    """
    segmentation = {}
    unit_conversion = {"mm": 1.0, "cm": 10.0}
    with open(file_path, 'r') as f:
        for line in f:
            m = re.search(r'pitch([XYZ])\s+(\d+\.?\d*)\s*(mm|cm)?', line, re.IGNORECASE)
            if m:
                axis = m.group(1).upper()
                size = float(m.group(2))
                unit = m.group(3) if m.group(3) else "mm"
                size *= unit_conversion.get(unit.lower(), 1.0)
                segmentation[axis] = size
                print(f"Extracted digitizer pitch for axis {axis}: {size} mm")
    return segmentation

def calculate_pitch(crystal_size, target_pitch):
    """
    Computes the best pitch for a given crystal size and target pitch.
    Iterates over possible repeat numbers and accepts only divisions with zero remainder (within tolerance).
    Returns a tuple (best_pitch, repeat_number).
    """
    best_pitch = 0
    min_diff = 999
    num_pitches = 1
    tol = 1e-20
    while True:
        pitch = crystal_size / num_pitches
        if pitch <= target_pitch and math.fmod(crystal_size, pitch) < tol:
            diff = abs(pitch - target_pitch)
            if diff <= min_diff:
                min_diff = diff
                best_pitch = pitch
        if best_pitch != 0 and best_pitch <= target_pitch:
            break
        elif num_pitches > 1000:
            print(f"ERROR! No pitch found in 1000 iterations! Size = {crystal_size} and desired pitch = {pitch}")
            break
        num_pitches += 1
    repeat_number = int(round(crystal_size / best_pitch)) if best_pitch != 0 else 0
    return best_pitch, repeat_number

def parse_arguments():
    """
    Parses command line arguments for the geometry processing script.
    
    Expected usage (example):
      python script.py -c XYZ -d digitizer.mac -i geometry_input.mac -o geometry_output.mac

    Short flags:
      -crp        Column Row PseudoCrystal (CRP) division string (e.g., XYZ)
      -d, --digitizer  Path to digitizer.mac file
      -i, --input      Path to input geometry file
      -o, --output     Path to output geometry file
    """
    # Create the ArgumentParser object with a description.
    parser = argparse.ArgumentParser(description="Process geometry file with segmentation parameters.")
    
    # Add the -crp argument with short flag -c. This is required.
    parser.add_argument("-crp", required=True, 
                        help="Column Row Layer (CRP) division string (e.g., XYZ) specifying the segmentation mapping.")
    
    # Add the --digitizer argument with short flag -d. This is required.
    parser.add_argument("-d", "--digitizer", required=True, 
                        help="Path to the digitizer.mac file containing segmentation parameters.")
    
    # Add the --input argument with short flag -i. This is required.
    parser.add_argument("-i", "--input", required=True, 
                        help="Path to the input geometry file.")
    
    # Add the --output argument with short flag -o. This is required.
    parser.add_argument("-o", "--output", required=True, 
                        help="Path to the output geometry file.")
    
    # Parse the command line arguments into a Namespace object.
    args = parser.parse_args()
    
    # Return the parsed values. They can be accessed via args.crp, args.digitizer, etc.
    return args.crp, args.digitizer, args.input, args.output


def build_crp_mapping(crp_str):
    """
    Builds a mapping for element -> assigned segmentation axis.
    Expected: first character for column, second for row, third for layer/pseudoCrystal (if present, else None or '0').
    """
    mapping = {}
    if len(crp_str) < 1:
        print("Error: crp_str must have at least 1 characters for column.")
        sys.exit(1)
    mapping['column'] = None if crp_str[0] == '0' else crp_str[0].upper()

    if len(crp_str) >= 2:
        mapping['row'] = None if crp_str[1] == '0' else crp_str[1].upper()
        if len(crp_str) >= 3:
            mapping['pseudoCrystal'] = None if crp_str[2] == '0' else crp_str[2].upper()
        else:
            mapping['pseudoCrystal'] = None
    else:
        mapping['row'] = None
        mapping['pseudoCrystal'] = None
    print(f"Using crp mapping: {mapping}")
    return mapping

def insert_repeater_lines(crp_mapping, global_update):
    """
    For each system (column, row, layer/pseudoCrystal) in the CRP mapping, builds the repeater lines.
    The repeater lines use the repeat number and the computed best pitch for the system’s assigned axis.
    The repeat vector is built so that only the component corresponding to the assigned axis is nonzero.
    Returns a list of repeater lines.
    """
    repeater_lines = []
    for system in crp_mapping:
        assigned_axis = crp_mapping[system]
        if assigned_axis is None:
            continue
        if assigned_axis in global_update:
            best_pitch = global_update[assigned_axis][1]
            system_repeat = global_update[assigned_axis][2]
        else:
            best_pitch = 0
            system_repeat = 0
        # Build repeat vector: only the component corresponding to assigned_axis is nonzero.
        vector = {"X": "0.0", "Y": "0.0", "Z": "0.0"}
        if assigned_axis == "X":
            vector["X"] = f"{best_pitch:.6f}"
        elif assigned_axis == "Y":
            vector["Y"] = f"{best_pitch:.6f}"
        elif assigned_axis == "Z":
            vector["Z"] = f"{best_pitch:.6f}"
        repeat_vector = f"{vector['X']} {vector['Y']} {vector['Z']}"
        repeater_lines.append(f"/gate/{system}/repeaters/insert\t\t\t\tlinear\n")
        repeater_lines.append(f"/gate/{system}/linear/setRepeatNumber\t\t\t{system_repeat}\n")
        repeater_lines.append(f"/gate/{system}/linear/setRepeatVector\t\t\t{repeat_vector} mm\n")
    return repeater_lines

def modify_geometry(input_file, segmentation, crp_mapping, output_file):
    """
    Processes the geometry file line by line.
    A new element block is detected when a line with '/gate/xxx/daughters/name' appears.
    For geometry lines (matching '/set?Length') in element blocks:
      - If a computed update for that axis exists in global_update, replace its numeric value.
      - Otherwise, if the geometry line's axis equals the assigned segmentation axis for the current block,
        compute the update and store it in global_update.
    Finally, the repeater block is inserted immediately after the LAST line that contains "/gate/pseudoCrystal/".
    """
    
    
    
    with open(input_file, 'r') as f:
        lines = f.readlines()

    modified_lines = []
    current_element = None  # "column", "row", or "layer"
    global_update = {}      # keyed by axis letter ("X", "Y", "Z"), with value (orig_value, best_pitch, repeat_number)
    first_system_index = None  # to track the last line index where "/gate/pseudoCrystal/" occurs

    modified_elements = []

    name_re = re.compile(r'/gate/[^/]+/daughters/name\s+(.*)', re.IGNORECASE)
    geom_re = re.compile(r'(/gate/([^/]+)/geometry/set)([XYZ])Length\s+(\d+\.?\d*)\s*(mm|cm)', re.IGNORECASE)

    for line in lines:
        # Detect new element block.

        name_match = name_re.search(line)


        if name_match:
            token = name_match.group(1).strip().lower()

            if  "column" in token:
                current_element = "column"
                if crp_mapping["column"] and "column" not in modified_elements:
                    modified_elements.append("column")
                    
            elif "row" in token:
                current_element = "row"
                if crp_mapping["row"] and  "row" not in modified_elements:
                    modified_elements.append("row")
                    
            elif "pseudo" in token:
                current_element = "pseudoCrystal"
                if crp_mapping["pseudoCrystal"] and "pseudoCrystal" not in modified_elements:
                    modified_elements.append("pseudoCrystal")
                    
            else:
                current_element = None
            modified_lines.append(line)

            continue

        # Process geometry lines if within an element block.
        geom_match = geom_re.search(line)
        if current_element and geom_match:
            element_in_line = geom_match.group(2).lower()
            if current_element.lower() not in element_in_line:
                modified_lines.append(line)
                continue

            prefix = geom_match.group(1)  # e.g., "/gate/column/geometry/set"
            cmd_axis = geom_match.group(3).upper()  # the axis letter in the command
            orig_value = float(geom_match.group(4))
            unit = geom_match.group(5).lower()
            if unit == "cm":
                orig_value *= 10

            if cmd_axis in global_update:
                new_value = global_update[cmd_axis][1]
                new_line = f"{prefix}{cmd_axis}Length\t\t\t{new_value:.6f} mm\n"
                modified_lines.append(new_line)
            else:
                assigned_axis = crp_mapping.get(current_element)
                if assigned_axis is not None and cmd_axis == assigned_axis:
                    target_pitch = segmentation.get(assigned_axis)
                    if target_pitch is None:
                        print(f"Warning: No digitizer pitch for axis {assigned_axis} for element {current_element}. Leaving line unchanged.")
                        modified_lines.append(line)
                        continue
                    best_pitch, repeat_number = calculate_pitch(orig_value, target_pitch)
                    global_update[cmd_axis] = (orig_value, best_pitch, repeat_number)
                    new_line = f"{prefix}{cmd_axis}Length\t\t\t{best_pitch:.6f} mm\n"
                    print(f"Extracted pitch for axis {assigned_axis} is {target_pitch} mm, the best pitch found is {best_pitch} mm and it will be repeated {repeat_number}")
                    modified_lines.append(new_line)
                else:
                    modified_lines.append(line)
        else:
            modified_lines.append(line)

    for element in ["column","row","pseudoCrystal"]:
        if crp_mapping[element] and (element not in modified_elements):
            print(f"Error: the macro does not contain any geometry element named '",element,"'")
            sys.exit(1)

    # Build repeater lines using the global update and crp mapping.
    repeater_lines = insert_repeater_lines(crp_mapping, global_update)

    # Insert the repeater block after the LAST occurrence of "/gate/pseudoCrystal/"

    first_system_index = next((i for i, line in enumerate(modified_lines) if '/gate/systems/' in line), None)
    if first_system_index is not None:
        modified_lines = modified_lines[:first_system_index] + ["\n","\n", "#Adding repeaters\n"]+ repeater_lines +["#End of repeaters\n","\n", "\n"]+ modified_lines[first_system_index:]

        
    else:

        modified_lines.extend(["\n","\n", "#Adding repeaters\n"]+ repeater_lines +["#End of repeaters\n","\n", "\n"])


    with open(output_file, 'w') as f:
        f.writelines(modified_lines)

if __name__ == "__main__":
    crp_str, digitizer_file, input_file, output_file = parse_arguments()
    crp_mapping = build_crp_mapping(crp_str)
    if crp_mapping['column']:
        print("Columns need to be modified ",crp_mapping['column'])
    if crp_mapping["row"]:
        print("rows need to be modified")
    if crp_mapping["pseudoCrystal"]:
        print("pC need to be modified")
   
    segmentation_params = extract_virtual_segmentation(digitizer_file)
    modify_geometry(input_file, segmentation_params, crp_mapping, output_file)

