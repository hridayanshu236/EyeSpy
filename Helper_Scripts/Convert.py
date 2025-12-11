import os
import glob

def convert_yolo_class_ids(input_file, output_file=None):
    """
    Convert YOLO class IDs in a label file.
    Changes class ID 15 to 0 and 16 to 1.
    
    Args:
        input_file (str): Path to the input YOLO label file
        output_file (str, optional): Path to save the converted file. 
                                   If None, overwrites the input file.
    """
    
    # Class ID mapping
    class_mapping = {0.0: 0, 1.0: 1}
    
    try:
        # Read the file
        with open(input_file, 'r') as file:
            lines = file.readlines()
        
        # Process each line
        converted_lines = []
        changes_made = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                converted_lines.append(line + '\n')
                continue
            
            # Split the line into components
            parts = line.split()
            
            if len(parts) != 5:
                print(f"Warning: Line {line_num} doesn't have 5 components: {line}")
                converted_lines.append(line + '\n')
                continue
            
            try:
                # Get the current class ID
                current_class_id = int(parts[0])
                
                # Check if we need to convert this class ID
                if current_class_id in class_mapping:
                    new_class_id = class_mapping[current_class_id]
                    parts[0] = str(new_class_id)
                    changes_made += 1
                    print(f"Line {line_num}: Changed class ID {current_class_id} → {new_class_id}")
                
                # Reconstruct the line
                converted_line = ' '.join(parts) + '\n'
                converted_lines.append(converted_line)
                
            except ValueError:
                print(f"Warning: Line {line_num} has invalid class ID: {parts[0]}")
                converted_lines.append(line + '\n')
        
        # Determine output file
        if output_file is None:
            output_file = input_file
        
        # Write the converted lines
        with open(output_file, 'w') as file:
            file.writelines(converted_lines)
        
        print(f"\nConversion complete!")
        print(f"Total changes made: {changes_made}")
        print(f"Output saved to: {output_file}")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"Error: {e}")


def convert_directory(directory_path):
    """
    Convert all .txt files in a directory.
    
    Args:
        directory_path (str): Path to directory containing YOLO label files
    """
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a valid directory.")
        return
    
    # Find all .txt files in the directory
    txt_files = glob.glob(os.path.join(directory_path, "*.txt"))
    
    if not txt_files:
        print(f"No .txt files found in '{directory_path}'")
        return
    
    print(f"Found {len(txt_files)} .txt files in '{directory_path}'")
    
    for file_path in txt_files:
        print(f"\nProcessing: {os.path.basename(file_path)}")
        convert_yolo_class_ids(file_path)


def batch_convert_files(file_list):
    """
    Convert multiple YOLO label files at once.
    
    Args:
        file_list (list): List of file paths to convert
    """
    for file_path in file_list:
        print(f"\nProcessing: {file_path}")
        convert_yolo_class_ids(file_path)


# Example usage
if __name__ == "__main__":
    # Convert all .txt files in a directory
    directory_path = "Label_augmented"  
    convert_directory(directory_path)
    
    # Single file conversion
    # convert_yolo_class_ids("specific_file.txt")
    
    # Optional: Create a backup with different name
    # convert_yolo_class_ids("labels.txt", "labels_converted.txt")
    
    # Batch conversion example
    # file_list = ["file1.txt", "file2.txt", "file3.txt"]
    # batch_convert_files(file_list)

    # 15 0.472222 0.498884 0.445106 0.452629
