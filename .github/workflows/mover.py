import json

with open('.github/workflows/mover.json', 'r') as file:
    data = json.load(file)
print(data)

for output, inputs in data.items():
    with open(output, 'w') as file:
        lines = []
        for inp in inputs:
            with open(inp, 'r') as inp_file:
                lines += inp_file.readlines()
                lines += '\n'
        file.writelines(lines)
