import argparse
import os
import subprocess
import contract_analysis
from utils.file_handler import get_latest_json, manage_intermediate_files, delete_intermediate_files, write_final_output
from obfuscation_techniques.opaque_predicate_obfuscation.obfuscate import process_files
from obfuscation_techniques.factory_based_contract.factory_based_contract_obfuscation import apply_obfuscation
from obfuscation_techniques.proxy_contract.proxy_interaction_obfuscation import process_proxy_files
from obfuscation_techniques.dynamic_function_dispatch.obfuscation import process_obfuscation
from obfuscation_techniques.high_to_low_conversion import process_contracts

def print_separator(title):
    """Prints a separator for better visibility."""
    print("\n" + "=" * 50)
    print(f"=== {title} ===")
    print("=" * 50)

def get_files_from_input(input_path):
    """Extract Solidity files from input (single file or folder)."""
    if os.path.isfile(input_path):
        if input_path.endswith('.sol'):
            return [input_path]
        else:
            print(f"Error: {input_path} is not a Solidity (.sol) file.")
            return []
    elif os.path.isdir(input_path):
        files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.sol')]
        if not files:
            print("Error: No Solidity (.sol) files found in the folder.")
        return files
    else:
        print("Error: Invalid input path.")
        return []

def syntax_analysis(file_path):
    """Perform syntax analysis using solcjs."""
    print_separator(f"Syntax Analysis for {file_path}")
    try:
        result = subprocess.run(
            [r"C:\Users\WELCOME\AppData\Roaming\npm\npx.cmd", "solcjs", "--bin", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Syntax Error:\n{result.stderr}")
            return False
        print(f"Syntax analysis passed.\n{result.stdout}")
        return True
    except FileNotFoundError:
        print("Error: Solidity compiler not found. Make sure it's installed.")
        return False

def semantic_analysis(file_path):
    """Perform semantic analysis using solcjs."""
    print_separator(f"Semantic Analysis for {file_path}")
    try:
        result = subprocess.run(
            [r"C:\Users\WELCOME\AppData\Roaming\npm\npx.cmd", "solcjs", "--abi", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            print(f"Semantic Error:\n{result.stderr}")
            return False
        print(f"Semantic analysis passed.\n{result.stdout}")
        return True
    except FileNotFoundError:
        print("Error: Solidity compiler not found. Make sure it's installed.")
        return False

def run_obfuscation(input_folder, intermediate_folder, output_folder, json_folder):
    """Handles sequential obfuscation techniques and file management."""
    latest_json_file = get_latest_json(json_folder)
    print_separator(f"Obfuscation Process (JSON: {latest_json_file})")

    print("\n🔹 Step 1: Opaque Predicate Obfuscation")
    process_files(input_folder, intermediate_folder, latest_json_file)

    print("\n🔹 Step 2: Dynamic Dispatch Obfuscation")
    process_obfuscation(intermediate_folder, latest_json_file, output_folder)
    delete_intermediate_files(intermediate_folder)

    print("\n🔹 Step 3: Factory-Based Contract Obfuscation")
    process_contracts(output_folder, intermediate_folder, latest_json_file)
    delete_intermediate_files(output_folder)

    print("\n🔹 Step 4: Proxy-Based Contract Obfuscation")
    process_proxy_files(intermediate_folder, output_folder, latest_json_file)
    delete_intermediate_files(intermediate_folder)

    print("\n🔹 Step 5: High-to-Low Conversion Obfuscation")
    apply_obfuscation(output_folder, latest_json_file)

    print_separator("Obfuscation Completed ✅")

def main():
    parser = argparse.ArgumentParser(description="Solidity Contract Analysis and Obfuscation Tool")
    parser.add_argument("input", help="Path to Solidity file or folder")
    args = parser.parse_args()

    input_path = args.input
    output_path = "output/obfuscated_contracts"
    intermediate_folder = "utils/intermediate_contracts"

    files = get_files_from_input(input_path)
    if not files:
        print("No valid files found for analysis. Exiting.")
        return

    for file in files:
        print_separator(f"Processing File: {file}")

        if not syntax_analysis(file):
            print(f"Skipping further checks for {file} due to syntax errors.")
            continue

        if not semantic_analysis(file):
            print(f"Skipping further checks for {file} due to semantic errors.")
            continue

        print(f"\n✅ {file} passed syntax and semantic analysis.")

    print_separator("Performing Interaction Analysis")
    contract_analysis.manual_analysis(os.path.dirname(file))  # Pass the folder containing the file

    print_separator("Starting Obfuscation Phase")
    run_obfuscation(input_path, intermediate_folder, output_path, "output/analysis_results")

    print_separator("All Analyses & Obfuscations Completed 🎉")

if __name__ == "__main__":
    main()
