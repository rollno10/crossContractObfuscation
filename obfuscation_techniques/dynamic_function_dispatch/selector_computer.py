import struct
import json
from eth_hash.auto import keccak  # Ethereum-compatible Keccak-256 hashing

def compute_obfuscated_selector(function_signature: str, salt: int) -> str:
    """
    Compute an obfuscated function selector using XOR with a salt.

    :param function_signature: Solidity function signature (e.g., "transfer(address,uint256)")
    :param salt: Obfuscation salt (integer)
    :return: Obfuscated function selector (hex string)
    """
    original_selector = get_function_selector(function_signature)
    salt_bytes = struct.pack(">I", salt)  # Convert salt to 4-byte format

    obfuscated_selector = bytes(a ^ b for a, b in zip(original_selector, salt_bytes))
    return "0x" + obfuscated_selector.hex()

def get_function_selector(function_signature: str) -> bytes:
    """
    Compute the first 4 bytes of the Keccak-256 hash of a function signature.

    :param function_signature: Solidity function signature
    :return: 4-byte function selector
    """
    return keccak(function_signature.encode())[:4]  # Compute Keccak-256 hash and get the first 4 bytes

def register_function(function_targets: dict, function_signature: str, salt: int, contract_address: str):
    """
    Register a function with its obfuscated selector to the target contract address.

    :param function_targets: Dictionary to store obfuscated selector mappings.
    :param function_signature: Solidity function signature.
    :param salt: Obfuscation salt (integer).
    :param contract_address: Target contract address.
    """
    obfuscated_selector = compute_obfuscated_selector(function_signature, salt)
    function_targets[obfuscated_selector] = {
        "function_signature": function_signature,
        "contract_address": contract_address,
    }
    print(f"✅ Registered: {function_signature} -> {obfuscated_selector} -> {contract_address}")

def export_registry(function_targets: dict, filename="selector_registry.json"):
    """
    Export the obfuscated selector registry to a JSON file.

    :param function_targets: Dictionary storing obfuscated selector mappings.
    :param filename: Name of the file to save.
    """
    with open(filename, "w") as f:
        json.dump(function_targets, f, indent=4)
    print(f"📂 Registry exported to {filename}")
