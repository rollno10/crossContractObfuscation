import os
import re
import argparse
import matplotlib.pyplot as plt

def extract_interaction_data(filepath):
    """Extract contract interaction complexity and gas cost using static analysis."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    complexity = 0
    gas_cost = 0

    # High-level calls
    high_calls = re.findall(r'\w+\.\w+\(', content)
    complexity += len(high_calls)
    gas_cost += len(high_calls)

    # Low-level calls
    low_calls = re.findall(r'\.(call|delegatecall|staticcall)\b', content)
    low_conditions = re.findall(r'if\s*\(.*\.(call|delegatecall|staticcall)', content)
    complexity += len(low_conditions) + len(low_calls)
    gas_cost += len(low_calls) + len(low_conditions) * 2

    # Opaque predicates
    opaque_preds = re.findall(r'if\s*\(.*(call|delegatecall|staticcall).*&&.*\)', content)
    complexity += len(opaque_preds)
    gas_cost += len(opaque_preds) * 2

    # Proxy patterns
    proxy_patterns = re.findall(r'(fallback|delegateTo|implementation|forwardTo|functionSelector)', content)
    complexity += len(set(proxy_patterns))
    gas_cost += len(proxy_patterns) * 2

    # Factory-related complexity
    factory_proxy = re.findall(r'new\s+Proxy\s*\(', content)
    complexity += len(factory_proxy)
    gas_cost += len(factory_proxy) * 4

    factory_new = re.findall(r'new\s+[A-Z]\w+', content)
    factory_create2 = re.findall(r'create2', content, re.IGNORECASE)
    complexity += len(factory_new)
    gas_cost += len(factory_new) * 2 + len(factory_create2) * 3

    return complexity, gas_cost

def percent_change(orig, obf):
    """Calculate percentage change."""
    if orig == 0 and obf > 0:
        return f"{(obf - orig) * 10:+.2f}%"
    elif orig == 0 and obf == 0:
        return "0%"
    else:
        return f"{(obf - orig) * 10:+.2f}%"

def compare_files(orig_file, obf_file):
    """Compare total complexity and gas cost between original and obfuscated contracts."""
    orig_complexity, orig_gas = extract_interaction_data(orig_file)
    obf_complexity, obf_gas = extract_interaction_data(obf_file)

    comp_change = percent_change(orig_complexity, obf_complexity)
    gas_change = percent_change(orig_gas, obf_gas)

    return os.path.basename(orig_file), orig_complexity, obf_complexity, comp_change, orig_gas, obf_gas, gas_change

def compare_folders(orig_folder, obf_folder):
    """Analyze complexity across multiple contract files and generate table & charts."""
    results = []

    for file in os.listdir(orig_folder):
        if file.endswith('.sol'):
            orig_path = os.path.join(orig_folder, file)
            obf_path = os.path.join(obf_folder, file)

            if os.path.exists(obf_path):
                results.append(compare_files(orig_path, obf_path))

    print_table(results)
    plot_bar_charts(results)

def print_table(data):
    """Print the comparison table in structured format."""
    print("\n Solidity Contract Complexity & Gas Cost Comparison\n")
    print("-" * 120)
    print(f"{'File Name':<20} | {'Orig. Complex.':>5} | {'Obf. Complex.':>5} | {'% Change':>10} | {'Orig. Gas':>5} | {'Obf. Gas':>5} | {'% Change':>10}")
    print("-" * 120)

    for entry in data:
        print(f"{entry[0]:<25} | {entry[1]:^10} | {entry[2]:^10} | {entry[3]:^10} | {entry[4]:^10} | {entry[5]:^10} | {entry[6]:^10}")

    print("-" * 120)

def plot_bar_charts(data):
    """Generate four bar charts for complexity and gas cost comparison with adjusted Y-axis ranges."""
    filenames = [entry[0] for entry in data]
    orig_complexity = [entry[1] for entry in data]
    obf_complexity = [entry[2] for entry in data]
    orig_gas = [entry[4] for entry in data]
    obf_gas = [entry[5] for entry in data]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Set Y-axis limits for complexity charts (range: 15)
    axes[0, 0].bar(filenames, orig_complexity, color='blue')
    axes[0, 0].set_title("Original Complexity")
    axes[0, 0].set_ylim(0, 15)

    axes[0, 1].bar(filenames, obf_complexity, color='green')
    axes[0, 1].set_title("Obfuscated Complexity")
    axes[0, 1].set_ylim(0, 15)

    # Set Y-axis limits for gas cost charts (range: 50)
    axes[1, 0].bar(filenames, orig_gas, color='red')
    axes[1, 0].set_title("Original Gas Cost")
    axes[1, 0].set_ylim(0, 50)

    axes[1, 1].bar(filenames, obf_gas, color='orange')
    axes[1, 1].set_title("Obfuscated Gas Cost")
    axes[1, 1].set_ylim(0, 50)

    # Improve readability for X-axis labels
    for ax in axes.flatten():
        ax.set_xticklabels(filenames, rotation=45, ha='right')
        ax.set_ylabel("Value")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare total contract complexity and gas cost.")
    parser.add_argument('--original', required=True, help="Path to original contract folder")
    parser.add_argument('--obfuscated', required=True, help="Path to obfuscated contract folder")
    args = parser.parse_args()

    compare_folders(args.original, args.obfuscated)
