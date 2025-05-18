import os
import re
from utils.file_handler import load_json
from .predicate_builder import get_predicate

def obfuscate_contract(contract_code, obfuscation_rules):
    """
    Inserts opaque predicates for specified interaction roles and types based on interaction_type in the JSON file.
    """
    lines = contract_code.split('\n')
    obfuscated_lines = []
    inside_function = False  # Track if we are inside a function
    predicate_applied = {}   # Track predicates applied per interaction type within a function

    for line in lines:
        stripped_line = line.strip()

        # Detect function declarations
        if re.match(r'\b(\w+)\.(\w+)\((.*?)\)', stripped_line):
            inside_function = True
            predicate_applied = {  # Reset tracking for a new function
                "high_level": False,
                "low_level": False,
                "interface_call": False,
                "delegate_call": False
            }
            obfuscated_lines.append(line)  # Add function declaration
            continue

        # Detect the end of the function
        if inside_function and stripped_line == "}":
            inside_function = False
            predicate_applied = {}  # Reset after function ends
            obfuscated_lines.append(line)  # Add closing brace
            continue

        # Apply predicates based on interaction types
        for rule in obfuscation_rules:
            role = rule.get("interaction_role", "").lower()  # initiator, middleware, executor
            interaction_type = rule.get("interaction_type", "").lower()  # high_level, low_level, etc.

            if not role or not interaction_type:
                continue  # Skip invalid rules

            # High-level interaction: Add predicate at the start of the function body
            if interaction_type == "high_level" and inside_function and not predicate_applied["high_level"]:
                predicate = get_predicate(role, "high_level")
                obfuscated_lines.append(f"        {predicate}")  # Place predicate logically
                predicate_applied["high_level"] = True
                break

            # Low-level interaction: Add predicate above low-level calls
            if interaction_type == "low_level" and re.search(r'(\w+)\.(call|staticcall)\((.*?)\)', stripped_line) and not predicate_applied["low_level"]:
                predicate = get_predicate(role, "low_level")
                obfuscated_lines.append(f"        {predicate}")
                predicate_applied["low_level"] = True
                break

            # Interface call: Add predicate above interface interactions
            if interaction_type == "interface_call" and re.search(r'\binterface\b', stripped_line) and not predicate_applied["interface_call"]:
                predicate = get_predicate(role, "interface_call")
                obfuscated_lines.append(f"        {predicate}")
                predicate_applied["interface_call"] = True
                break

            # Delegate call: Add predicate above delegate calls
            if interaction_type == "delegate_call" and re.search(r'(\w+)\.delegatecall\((.*?)\)', stripped_line) and not predicate_applied.get("delegate_call", False):
                predicate = get_predicate(role, "delegate_call")
                obfuscated_lines.append(f"        {predicate}")
                predicate_applied["delegate_call"] = True
                break

        # Add the original line to the output
        obfuscated_lines.append(line)

    return '\n'.join(obfuscated_lines)

    
def process_files(contract_folder, output_folder, json_file):
    """
    Reads Solidity files, applies obfuscation predicates, and writes results.
    :param contract_folder: Folder containing Solidity files to obfuscate.
    :param output_folder: Folder to save obfuscated contract files.
    :param json_file: JSON file containing obfuscation rules with interaction types.
    """
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