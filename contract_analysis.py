import os
import re
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Configure logging for better traceability
logging.basicConfig(level=logging.INFO)

def analyze_contract(contract_path):
    interactions = []
    contract_name = os.path.basename(contract_path)

    try:
        with open(contract_path, 'r', encoding='utf-8') as file:
            code = file.read()
    except Exception as e:
        logging.error(f"Error reading file {contract_path}: {e}")
        return []

    # Pre-compiled regex patterns for efficiency
    high_level_pattern = re.compile(r'\b(\w+)\.(\w+)\((.*?)\)')
    low_level_pattern = re.compile(r'(\w+)\.(call|staticcall)\((.*?)\)')
    delegate_pattern = re.compile(r'(\w+)\.delegatecall\((.*?)\)')
    factory_pattern = re.compile(r'new\s+(\w+)\s*\((.*?)\)')
    proxy_keywords = [
        re.compile(r'\bdelegatecall\b', re.IGNORECASE),
        re.compile(r'\bupgradeTo\b', re.IGNORECASE),
        re.compile(r'\bimplementation\b', re.IGNORECASE),
        re.compile(r'\bgetImplementation\b', re.IGNORECASE),
        re.compile(r'\bproxyAdmin\b', re.IGNORECASE),
        re.compile(r'\b_upgrade\b', re.IGNORECASE)
    ]

    # Determine interaction role based on contract behavior
    def determine_role(code):
        if "msg.sender" in code and "require" in code:
            return "initiator"
        elif any(keyword.search(code) for keyword in proxy_keywords):
            return "middleware"
        elif re.search(r'\.delegatecall\(', code):
            return "executor"
        else:
            return "unknown"

    # Validating Solidity file
    if not re.search(r'pragma\s+solidity', code):
        logging.info(f"Skipping non-Solidity file: {contract_name}")
        return []

    # Determine interaction role
    interaction_role = determine_role(code)

    # Analyze interactions
    # 1. High-Level Calls
    high_level_calls = high_level_pattern.findall(code)
    for obj, func, args in high_level_calls:
        if func not in ["call", "delegatecall", "staticcall"]:  # Exclude low-level calls
            interactions.append({
                "caller": contract_name,
                "callee": obj,
                "function": func,
                "interaction_type": "high_level",  # Updated field
                "interaction_role": interaction_role,  # Added role
                "function_signature": f"{func}({args})",  # Extra field
                "contract_address": "0x0000000000000000000000000000000000000000"  # Placeholder for high-level interaction
            })

    # 2. Low-Level Calls (call, staticcall ONLY)
    low_level_calls = low_level_pattern.findall(code)
    for callee, call_type, args in low_level_calls:
        interactions.append({
            "caller": contract_name,
            "callee": callee,
            "function": call_type,
            "interaction_type": "low_level",  # Updated field
            "interaction_role": interaction_role,  # Added role
            "function_signature": f"{call_type}({args})",  # Extra field
            "contract_address": callee  # Using callee directly as contract address for low-level calls
        })

    # 3. Delegatecall ONLY
    delegate_calls = delegate_pattern.findall(code)
    for callee, _ in delegate_calls:
        interactions.append({
            "caller": contract_name,
            "callee": callee,
            "function": "delegatecall",
            "interaction_type": "delegate_call",  # Updated field
            "interaction_role": interaction_role  # Added role
        })

    # 4. Factory Deployments
    factory_calls = factory_pattern.findall(code)
    for callee, _ in factory_calls:
        interactions.append({
            "caller": contract_name,
            "callee": callee,
            "interaction_type": "factory_deployment",  # Updated field
            "interaction_role": interaction_role  # Added role
        })

    # 5. Proxy Pattern Detection
    if any(keyword.search(code) for keyword in proxy_keywords):
        interactions.append({
            "caller": contract_name,
            "interaction_type": "proxy",  # Updated field
            "interaction_role": "middleware",  # Added role (proxy -> middleware)
            "details": "Detected keywords indicating proxy pattern"
        })

    return interactions

def manual_analysis(folder_path):
    all_interactions = []

    # Analyze files concurrently for better performance
    def process_file(path):
        return analyze_contract(path)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_file, os.path.join(folder_path, filename))
            for filename in os.listdir(folder_path) if filename.endswith(".sol")
        ]
        for future in futures:
            all_interactions.extend(future.result())

    # Create the output directory if it doesn't exist
    output_dir = os.path.join("output", "analysis_results")
    os.makedirs(output_dir, exist_ok=True)

    # Save the final JSON file in the output/analysis_results folder
    output_file = os.path.join(output_dir, f"interaction_{int(time.time())}.json")
    with open(output_file, "w", encoding='utf-8') as json_file:
        json.dump({"interactions": all_interactions}, json_file, indent=4)

    logging.info(f"✅ Manual Analysis Completed Successfully. Results saved to {output_file}")
