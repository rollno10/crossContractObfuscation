import os
import re
import json

def generate_obfuscated_proxy(contract_code):
    """
    Generate a Solidity proxy contract that preserves functionality, adds complexity, and incorporates obfuscation.
    """
    lines = contract_code.split('\n')
    obfuscated_lines = []
    skip_implementation_block = False
    inside_function = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect and replace the implementation() function
        if re.search(r'\bfunction\s+implementation\s*\(\)\s*(public|external)?\s*(view)?\s*returns\s*\(\s*address\s*\)', stripped) or re.search(r'\baddress\s+public\s+implementation\s*;', stripped):
            obfuscated_lines.append("    function implementation() external view returns (address) {")
            obfuscated_lines.append("        address fakeImplementation = address(uint160(uint256(keccak256(abi.encodePacked(blockhash(block.number - 1), msg.sender)))));")
            obfuscated_lines.append("        return fakeImplementation;")
            obfuscated_lines.append("    }")
            obfuscated_lines.append("    function realImplementation() public view onlyAdmin returns (address) {")
            obfuscated_lines.append("        return _implementation;")
            obfuscated_lines.append("    }")
            skip_implementation_block = True
            inside_function = True
            continue

        if skip_implementation_block:
            if '{' in stripped:
                inside_function = True
            if '}' in stripped and inside_function:
                skip_implementation_block = False
                inside_function = False
            continue

        # Replace fallback function with obfuscated logic
        if re.search(r'\bfallback\s*\(\s*\)\s*(external|public)?', stripped):
            obfuscated_lines.append("    fallback() external payable {")
            obfuscated_lines.append("        address impl = _getImplementation(msg.sig);")
            obfuscated_lines.append("        require(impl != address(0), \"Invalid implementation\");")
            obfuscated_lines.append("        (bool success, ) = impl.delegatecall(msg.data);")
            obfuscated_lines.append("        require(success, \"Delegatecall to logic contract failed\");")
            obfuscated_lines.append("        address nextProxy = getNextProxy();")
            obfuscated_lines.append("        require(nextProxy != address(0), \"Next proxy invalid\");")
            obfuscated_lines.append("        (bool success2, ) = nextProxy.delegatecall(msg.data);")
            obfuscated_lines.append("        require(success2, \"Nested delegatecall failed\");")
            continue

        # Default: keep original line
        obfuscated_lines.append(line)

    # Add receive() function if not present
    if "receive() external payable" not in contract_code:
        obfuscated_lines.append("    receive() external payable {}")

    # Add helper functions for dynamic routing
    if "_getImplementation" not in contract_code and "getNextProxy" not in contract_code:
        helper_code = """

function _getImplementation(bytes4 selector) internal view returns (address) {

    if (selector == bytes4(keccak256("someFunctionSignature()"))) {
        return 0x1234567890123456789012345678901234567890; 
    }
    return _implementation; 
}

function getNextProxy() internal view returns (address) {
    return address(0xBEEFDEAD);
}

modifier onlyAdmin() {
    require(msg.sender == _admin, "Only admin can call this function");
    _;
}
""".strip()
        obfuscated_lines.append(helper_code)

    return '\n'.join(obfuscated_lines)

def process_proxy_files(contract_folder, output_folder, json_file):
    """
    Process Solidity contracts to obfuscate proxy and non-proxy files, ensuring all are written to output.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load interactions from the JSON file
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
            interactions = data.get("interactions", [])
    except Exception as e:
        print(f" Error loading JSON file: {e}")
        return

    # Iterate through all contracts in the folder
    for filename in os.listdir(contract_folder):
        if not filename.endswith(".sol"):
            continue

        input_path = os.path.join(contract_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # Read the contract code
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                contract_code = f.read()
        except Exception as e:
            print(f" Failed to read contract file {filename}: {e}")
            continue

        # Check if this contract matches a "proxy" interaction
        is_proxy = any(
            interaction.get("caller") == filename and interaction.get("interaction_type") == "proxy"
            for interaction in interactions
        )

        if is_proxy:
            # Generate obfuscated proxy contract
            obfuscated_code = generate_obfuscated_proxy(contract_code)
            print(f" Processed (proxy): {filename}")
        else:
            # Write the contract as-is or apply placeholder obfuscation
            obfuscated_code = contract_code
            print(f" Processed (non-proxy): {filename}")

        # Write the output
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(obfuscated_code)
            print(f" Contract saved to: {output_path}")
        except Exception as e:
            print(f" Failed to save contract {filename}: {e}")
