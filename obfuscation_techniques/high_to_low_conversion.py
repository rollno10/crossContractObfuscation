import os
import re
import logging
from eth_utils import function_signature_to_4byte_selector
from solcx import install_solc, set_solc_version, compile_standard
from utils.file_handler import load_json

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Install and set the appropriate version of solc (if not already installed)
install_solc("0.8.20")  
set_solc_version("0.8.20")  

# Built-in functions that need special handling (add more as needed)
BUILT_IN_FUNCTIONS = ['transfer', 'approve', 'mint', 'transferFrom', 'safeTransfer', 'safeApprove']

def extract_interface_calls(source_code):
    """
    Extracts function calls in the form of 'address.function(arguments);' from source code.
    """
    pattern = re.compile(r'(\w+)\.(\w+)\(([^)]*)\);')
    matches = pattern.findall(source_code)
    return [(f"{m[0]}.{m[1]}({m[2]});", m[0], m[1], m[2]) for m in matches]

def get_function_selectors(ast_node):
    """
    Generates a dictionary of function selectors for each function in the contract.
    """
    selectors = {}

    def traverse(node):
        if isinstance(node, dict):
            if node.get("nodeType") == "FunctionDefinition" and node.get("kind") == "function":
                name = node.get("name")
                params = node.get("parameters", {}).get("parameters", [])
                param_types = [p.get("typeDescriptions", {}).get("typeString", "") for p in params]
                param_sig = ",".join(param_types)
                signature = f"{name}({param_sig})"
                selector = function_signature_to_4byte_selector(signature).hex()
                selectors[name] = selector
            for value in node.values():
                traverse(value)
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    traverse(ast_node)
    return selectors

def convert_calls_to_low_level(source_code, selectors):
    """
    Converts high-level function calls to low-level calls using the selector.
    """
    calls = extract_interface_calls(source_code)
    for full_call, var, func, args in calls:
        # Handle built-in functions like transfer, approve, mint, etc.
        if func in BUILT_IN_FUNCTIONS:
            if func == 'transfer':
                low_call = (
                    f'(bool success, ) = {var}.call{{value: {args.strip()}}}("");\n'
                    f'require(success, "Transfer failed");'
                )
            else:
                low_call = (
                    f'(bool success, ) = {var}.call(abi.encodeWithSignature("{func}({args})"));\n'
                    f'require(success, "{func} failed");'
                )
        else:
            # For custom functions, use selector encoding
            selector = selectors.get(func)
            if not selector:
                logging.warning(f"Function selector not found for: {func}")
                continue

            # Convert to low-level call with selector
            low_call = (
                f'(bool success, ) = {var}.call(abi.encodeWithSelector(0x{selector}, {args.strip()}));\n'
                f'require(success, "Call failed");'
            )
        
        # Replace the high-level call with the low-level version
        source_code = source_code.replace(full_call, low_call)
    
    return source_code

def compile_ast(source_code):
    """
    Compiles Solidity code into an AST, allowing us to extract function selectors.
    """
    compiled = compile_standard({
        "language": "Solidity",
        "sources": {
            "Temp.sol": {"content": source_code}
        },
        "settings": {"outputSelection": {"*": {"*": ["*"], "": ["ast"]}}}
    })
    return compiled["sources"]["Temp.sol"]["ast"]

def get_interaction_type(contract_file, interaction_data):
    """
    Get the interaction type from the interaction data (high-level, low-level, etc.).
    """
    for interaction in interaction_data:
        if interaction.get("caller") == contract_file:
            return interaction.get("interaction_type")
    return None

def process_contracts(input_folder, output_folder, json_path):
    """
    Process all contracts in the input folder, convert high-level calls to low-level, and save to output folder.
    Write all contracts to output, even if obfuscation is not performed.
    """
    interaction_data = load_json(json_path)  #  Custom loader here

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    selector_cache = {}  # Cache to store selectors for reusability

    for filename in os.listdir(input_folder):
        if filename.endswith(".sol"):
            interaction_type = get_interaction_type(filename, interaction_data)

            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            with open(input_path, "r") as f:
                contract = f.read()

            try:
                if interaction_type == "high_level":
                    logging.info(f"Processing {filename} for high-level call conversion...")
                    ast = compile_ast(contract)  # Get the AST for the contract
                    selectors = get_function_selectors(ast)  # Extract function selectors
                    converted_code = convert_calls_to_low_level(contract, selectors)  # Convert high-level calls
                else:
                    logging.info(f"No obfuscation applied to {filename} (interaction_type: {interaction_type})")
                    converted_code = contract  # Keep the original contract unchanged
                
                # Write the contract (processed or unchanged) to the output folder
                with open(output_path, "w") as f_out:
                    f_out.write(converted_code)
                
                logging.info(f"Saved: {output_path}")
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")
