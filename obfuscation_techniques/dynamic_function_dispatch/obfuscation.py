import os
import json
import re
import secrets  
from .selector_computer import register_function, export_registry, compute_obfuscated_selector

def obfuscate_contract(contract_code: str, obfuscation_rules: list, function_targets: dict) -> str:
    """ Injects function selector validation before execution."""

    lines = contract_code.split("\n")
    modified_lines = []

    for line in lines:
        stripped_line = line.strip()

        # Detect Solidity function definitions correctly
        match = re.match(r'function\s+(\w+)\s*\(([^)]*)\)', stripped_line)
        if match:
            function_name = match.group(1)
            function_signature = f"{function_name}({match.group(2)})"
            salt = secrets.randbelow(4294967295 + 1)  # Generate random salt
            obfuscated_selector = compute_obfuscated_selector(function_signature, salt)
            
            # Register obfuscated selector in function_targets
            register_function(function_targets, function_signature, salt, "")

            # Inject validation logic before function execution
            modified_lines.append(line)  # Add function declaration
            modified_lines.append(
                f"        require(msg.sig == bytes4(keccak256('{function_signature}')), 'Invalid function selector');"
            )
            continue

        # Detect low-level calls (call, delegatecall, staticcall)
        low_level_match = re.search(r'(\w+)\.(call|staticcall|delegatecall)\((.*?)\)', stripped_line)
        if low_level_match:
            salt = secrets.randbelow(4294967295 + 1)  # Generate random salt
            obfuscated_selector = compute_obfuscated_selector("low_level_call", salt)

            # Replace direct low-level call with dispatch execution
            modified_lines.append(
                f"        dispatchFunction(bytes4(keccak256('{obfuscated_selector}')), abi.encodePacked({low_level_match.group(1)}));"
            )
            continue

        # If no match, add the original line
        modified_lines.append(line)

    return "\n".join(modified_lines)

def process_obfuscation(input_folder: str, json_file: str, output_folder: str):

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load obfuscation rules
    with open(json_file, "r", encoding="utf-8") as f:
        obfuscation_rules = json.load(f).get("interactions", [])

    for filename in os.listdir(input_folder):
        if filename.endswith(".sol"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # Read Solidity contract code
            with open(input_path, "r", encoding="utf-8") as f:
                contract_code = f.read()

            # Store obfuscated function selectors
            function_targets = {}

            # Apply obfuscation technique
            obfuscated_code = obfuscate_contract(contract_code, obfuscation_rules, function_targets)

            # Export selector registry for debugging & transparency
            export_registry(function_targets, filename=os.path.join(output_folder, "selector_registry.json"))

            # Write the obfuscated contract
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(obfuscated_code)

            print(f"✅ Processed: {filename}")

    print(f" Obfuscation completed. Check the '{output_folder}' folder.")
