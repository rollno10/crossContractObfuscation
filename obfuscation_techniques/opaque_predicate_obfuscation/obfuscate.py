import os
import re
from utils.file_handler import load_json
from .predicate_builder import get_predicate

def obfuscate_contract(contract_code, obfuscation_rules):
    lines = contract_code.split('\n')
    obfuscated_lines = []
    inside_function = False  # Track if we are inside a function
    predicate_applied = {}   # Track predicates applied per interaction type within a function

    for line in lines:
        stripped_line = line.strip()

        # Detect function declarations
        if re.match(r'^\s*function\s+\w+\s*\(.*\)', stripped_line):  
            inside_function = True
            predicate_applied = {  
                "high_level": False,
                "low_level": False,
                "interface_call": False,
                "delegate_call": False
            }
            obfuscated_lines.append(line)  
            continue

        # Apply predicates based on interaction types
        for rule in obfuscation_rules:
            role = rule.get("interaction_role", "").lower()
            interaction_type = rule.get("interaction_type", "").lower()

            if not role or not interaction_type:
                continue  # Skip invalid rules

            if inside_function:  
                # High-level interaction: Add predicate at the start of function body  
                if interaction_type == "high_level" and not predicate_applied["high_level"]:
                    predicate = get_predicate(role, "high_level")
                    obfuscated_lines.append(f"        {predicate}")  
                    predicate_applied["high_level"] = True

                # Check for low-level calls and insert predicates  
                elif interaction_type == "low_level" and re.search(r'\b(call|staticcall)\b', stripped_line) and not predicate_applied["low_level"]:
                    predicate = get_predicate(role, "low_level")
                    obfuscated_lines.append(f"        {predicate}")
                    predicate_applied["low_level"] = True

                # Check for interface calls  
                elif interaction_type == "interface_call" and "interface" in stripped_line and not predicate_applied["interface_call"]:
                    predicate = get_predicate(role, "interface_call")
                    obfuscated_lines.append(f"        {predicate}")
                    predicate_applied["interface_call"] = True

                # Check for delegate calls  
                elif interaction_type == "delegate_call" and re.search(r'\bdelegatecall\b', stripped_line) and not predicate_applied["delegate_call"]:
                    predicate = get_predicate(role, "delegate_call")
                    obfuscated_lines.append(f"        {predicate}")
                    predicate_applied["delegate_call"] = True

        # Detect function ending and insert extra closing brace if needed
        if inside_function and stripped_line == "}":
            inside_function = False
            if predicate_applied:
                obfuscated_lines.append("        }") 
            obfuscated_lines.append(line)  
            continue

        # Add the original line to the output
        obfuscated_lines.append(line)

    return '\n'.join(obfuscated_lines)

def process_files(contract_folder, output_folder, json_file):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load obfuscation rules from JSON file
    obfuscation_rules = load_json(json_file)
    if not obfuscation_rules:
        print(f"Error: Unable to load obfuscation rules from {json_file}.")
        return

    for filename in os.listdir(contract_folder):
        if filename.endswith(".sol"):
            input_path = os.path.join(contract_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # Read the contract code
            with open(input_path, "r", encoding="utf-8") as f:
                contract_code = f.read()

            # Apply obfuscation rules to the contract code
            obfuscated_code = obfuscate_contract(contract_code, obfuscation_rules)

            # Write the obfuscated contract to the output folder
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(obfuscated_code)

            print(f"Processed: {filename}")
