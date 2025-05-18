import os
import re
import random
from utils.file_handler import load_json

FACTORY_TEMPLATE = '''
contract {factory_name} {{
    function deploy(uint256 route, bytes32 salt, address arg1, uint256 arg2, uint256 dummyArg1, string memory dummyArg2) public returns (address) {{
        if (route == 0) {{
            return address(new {target_contract}(arg1, arg2));
        }} else if (route == 1) {{
            return address(new {target_contract}(arg1, arg2)); 
        }} else {{
            return Create2.deploy(salt, abi.encodePacked(type({target_contract}).creationCode, abi.encode(arg1, arg2)));
        }}
    }}
}}
'''

def ensure_output_dir():
    """Ensures the output directory exists."""
    output_dir = "output/obfuscated_contracts"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def generate_factory(target_contract, factory_name):
    """Generates a Solidity factory contract based on the obfuscation technique."""
    return FACTORY_TEMPLATE.format(target_contract=target_contract, factory_name=factory_name)

def apply_obfuscation(input_folder, json_file):
    """Applies obfuscation to Solidity contracts dynamically."""
    output_dir = ensure_output_dir()

    try:
        analysis = load_json(json_file)  # Load JSON data from the file path
        interactions = analysis if isinstance(analysis, list) else analysis.get("interactions", [])
    except FileNotFoundError:
        print(f"Analysis file not found: {json_file}")
        return
    except Exception as e:
        print(f"Error loading or parsing JSON file: {e}")
        return

    for filename in os.listdir(input_folder):
        if not filename.endswith(".sol"):
            continue

        file_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_dir, filename)

        with open(file_path, "r") as f:
            content = f.read()

        # Identify all contract instantiations dynamically
        pattern = r"new\s+(\w+)\((.*?)\)"
        matches = re.findall(pattern, content)

        factory_definitions = ""

        for contract_name, args in matches:
            factory_name = f"ObfuscatedFactory_{contract_name}"
            factory_code = generate_factory(contract_name, factory_name)

            salt = f"keccak256(abi.encodePacked(block.timestamp, {args}))"
            route = random.randint(0, 2)
            dummy_arg1 = random.randint(0, 100)
            dummy_arg2 = '"ObfuscatedParam"'

            original = f"new {contract_name}({args})"
            replacement = (
                f"{factory_name}().deploy({route}, {salt}, {args}, {dummy_arg1}, {dummy_arg2})"
            )
            content = content.replace(original, replacement)

            factory_definitions += "\n" + factory_code

        content += "\n" + factory_definitions

        with open(output_path, "w") as f:
            f.write(content)

        print(f"✅ Obfuscated contract written to {output_path}")
