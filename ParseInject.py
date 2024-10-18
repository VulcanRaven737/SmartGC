import sys
import json
import parser

def inject_deallocation_code(input_file: str, output_file: str, json_file: str):
    print("Loading deallocation points from JSON file...")
    with open(json_file, 'r') as f:
        deallocation_data = json.load(f)
    print("Deallocation points loaded successfully.")

    deallocation_points = deallocation_data['deallocations']

    print("Reading original source code...")
    with open(input_file, 'r') as f:
        source_code = f.readlines()
    print("Original source code read successfully.")

    current_function = None
    function_start_pattern = "{"
    function_end_pattern = "}"
    brace_count = 0

    with open(output_file, 'w') as f:
        print("Injecting deallocation code...")
        for i, line in enumerate(source_code, start=1):
            # Track function scope
            if "(" in line and ")" in line and "{" in line:
                current_function = line.split("(")[0].strip().split()[-1]
                brace_count = 1
            elif "{" in line:
                brace_count += line.count("{")
            elif "}" in line:
                brace_count -= line.count("}")
                if brace_count == 0:
                    current_function = None

            f.write(line)
            
            for deallocation_point in deallocation_points:
                if (i == deallocation_point['line_number'] and 
                    current_function == deallocation_point['function_name']):
                    variable_name = deallocation_point['variable_name']
                    f.write(f'\tfree({variable_name});\n')
                    print(f"Freeing memory for variable {variable_name} at line {i} in function {current_function}")

        print("Deallocation code injected successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python preprocess.py input_file output_file json_file")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    json_file = sys.argv[3]

    parser.main(input_file, json_file)
    inject_deallocation_code(input_file, output_file, json_file)