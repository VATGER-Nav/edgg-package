import json
import os


def extract_file_path(import_statement):
    if "#import " in import_statement:
        file_path = import_statement.split("#import ")[1]
        # Remove leading/trailing whitespace and newlines from the file path
        file_path = file_path.strip()
        return file_path
    else:
        return None


def processImport(line, input_file):
    try:
        file_path = extract_file_path(line)
        print(file_path),

        if file_path:
            file_path_is_file = os.path.isfile(file_path)
            if file_path_is_file:
                with open(file_path, "r") as file:
                    lines = file.readlines()
                    file_content = ''.join(lines) + '\n'
                    return file_content
            else:
                # find all files in folder
                txt_files = []
                for root, _, files in os.walk(file_path):
                    for file in files:
                        if file.endswith(".txt"):
                            textfile_path = os.path.join(root, file)
                            with open(textfile_path, "r") as txt_file:
                                current_txt_file_lines = txt_file.readlines()
                                txt_files.extend(current_txt_file_lines)
                        txt_files.extend("\n")
                return txt_files
        return ""
    except FileNotFoundError:
        print("Error in. ", input_file.name)
        return f"# File {input_file} could no be imported\n"


with open(".github/workflows/mover.json", "r") as file:
    data = json.load(file)

for output, inputs in data.items():
    with open(output, "w") as file:
        lines = []
        for input in inputs:
            with open(input, "r") as input_file:
                for line in input_file:
                    if "#import" in line:
                        # replace "#import *" line with respective file
                        lines += processImport(line, input_file)

                    else:
                        lines += line
                lines += "\n\n"

        file.writelines(lines)
