import os
import tkinter as tk
from tkinter import filedialog

def read_gcode(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

def find_layers(gcode_lines, layer_height):
    layers = []
    current_height = 0
    for index, line in enumerate(gcode_lines):
        if line.startswith('G1') and 'Z' in line:
            parts = line.split()
            for part in parts:
                if part.startswith('Z'):
                    current_height = float(part[1:])
                    if current_height % layer_height < layer_height:
                        layers.append((current_height, index))
                    break
    return layers

def extract_start_commands(gcode_lines):
    start_commands = []
    for line in gcode_lines:
        if line.startswith(';'):
            continue  # Skip comments
        if any(command in line for command in ['G1', 'G92', 'G28']) and 'E' in line:
            break  # Stop at the first movement involving the extruder
        if not any(command in line for command in ['G1', 'G92', 'G28']):
            start_commands.append(line)
    return start_commands

def edit_gcode(gcode_lines, layers, fail_height, measured_height, layer_height, start_commands):
    fail_layer = None
    min_diff = float('inf')  # Initialize minimum difference as infinity
    for height, index in layers:
        diff = abs(height - fail_height)
        if diff < min_diff:
            min_diff = diff
            fail_layer = index

    if fail_layer is None:
        raise ValueError("Fail height is above the maximum height in the G-code")

    # Adjust start commands to set the current height and move to failure height
    z_adjustment_commands = [
        'G92 Z{:.2f} ; Set current Z position to user-measured height\n'.format(measured_height),
        'G28 X Y ; Home X and Y axis\n',
        'G1 Z{:.2f} ; Move to failure height\n'.format(fail_height)
    ]

    edited_gcode = start_commands + z_adjustment_commands + gcode_lines[fail_layer:]
    return edited_gcode

def upload_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title="Select G-code file")
    return file_path

def download_gcode(gcode_lines, gcode_path):
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    download_path = filedialog.asksaveasfilename(
        defaultextension=".gcode",
        initialfile='resume_' + os.path.basename(gcode_path),
        filetypes=[("G-code files", "*.gcode")],
        title="Save Edited G-code As"
    )

    root.destroy()  # Close the Tkinter root window

    if download_path.strip() != "":
        with open(download_path, 'w') as file:
            file.writelines(gcode_lines)
        print("The edited G-code file has been saved to:", download_path)
    else:
        print("No valid path specified. The edited G-code file has not been saved.")

def main():
    root = tk.Tk()
    root.title("G-code Editor")

    def process_gcode():
        gcode_path = upload_file()
        if gcode_path:
            # Generate the output path by prefixing "resume_" to the original filename
            output_filename = 'resume_' + os.path.basename(gcode_path)

            layer_height = float(layer_height_entry.get())
            fail_height = float(fail_height_entry.get())
            measured_height = float(measured_height_entry.get())

            # Read the original G-code file
            gcode_lines = read_gcode(gcode_path)

            # Extract start commands from the original G-code file
            start_commands = extract_start_commands(gcode_lines)

            # Find layer start points
            layers = find_layers(gcode_lines, layer_height)

            # Edit the G-code to resume the print from the fail height
            edited_gcode = edit_gcode(gcode_lines, layers, fail_height, measured_height, layer_height, start_commands)

            # Download the edited G-code file
            download_gcode(edited_gcode, gcode_path)
            root.destroy()

    # GUI Layout
    tk.Label(root, text="Layer Height (mm):").grid(row=0, column=0)
    layer_height_entry = tk.Entry(root)
    layer_height_entry.grid(row=0, column=1)

    tk.Label(root, text="Fail Height (mm):").grid(row=1, column=0)
    fail_height_entry = tk.Entry(root)
    fail_height_entry.grid(row=1, column=1)

    tk.Label(root, text="Measured Height (mm):").grid(row=2, column=0)
    measured_height_entry = tk.Entry(root)
    measured_height_entry.grid(row=2, column=1)

    process_button = tk.Button(root, text="Process G-code", command=process_gcode)
    process_button.grid(row=3, column=0, columnspan=2)

    root.mainloop()

if __name__ == "__main__":
    main()
