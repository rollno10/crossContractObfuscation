import os
import json

def get_latest_json(folder_path):
    """
    Fetch the latest JSON file from the specified folder.
    """
    try:
        # List all JSON files in the folder
        json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]

        if not json_files:
            raise FileNotFoundError("No JSON files found in the folder.")

        # Sort JSON files by modification time
        json_files = sorted(json_files, key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
        latest_file = json_files[0]
        return os.path.join(folder_path, latest_file)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except PermissionError:
        raise PermissionError("Permission denied while accessing the folder.")
    except Exception as e:
        raise Exception(f"Unexpected error while fetching JSON file: {e}")


def load_json(file_path):
    """
    Load JSON data from a file and extract the 'interactions' list if available.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            # Validate that the root is a dictionary containing a list under 'interactions'
            if not isinstance(data, dict):
                raise ValueError("Invalid JSON structure: Root element is not a dictionary.")
            if "interactions" not in data:
                raise ValueError("Invalid JSON structure: Missing 'interactions' key.")
            if not isinstance(data["interactions"], list):
                raise ValueError("Invalid JSON structure: 'interactions' is not a list.")

            # Return the list of interactions
            return data["interactions"]
    except FileNotFoundError:
        raise FileNotFoundError(f"File {file_path} not found.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON from {file_path}. Error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error while loading JSON: {e}")


def manage_intermediate_files(folder_path):
    """
    Retrieves Solidity files from the intermediate folder.
    """
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.sol')]


def delete_intermediate_files(folder_path):
    """
    Deletes Solidity files in the intermediate folder.
    """
    for file in os.listdir(folder_path):
        if file.endswith(".sol"):
            os.remove(os.path.join(folder_path, file))
    print(f"Deleted intermediate files in {folder_path}.")


def write_final_output(output_folder, file_name, code):
    """
    Writes the final obfuscated contract to the output folder.
    """
    output_path = os.path.join(output_folder, file_name)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"✅ Final output written to {output_path}")
