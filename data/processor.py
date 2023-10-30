import json

# Input CSV file and output text file names
input_json_file = 'medical_meadow_wikidoc_medical_flashcards.json'
output_txt_file = 'output.txt'

# Open the input JSON file for reading
with open(input_json_file, 'r', encoding='utf-8') as json_file:
    data = json.load(json_file)

# Open the output text file for writing
with open(output_txt_file, 'w', encoding='utf-8') as txt_file:
    for entry in data:
        if 'input' in entry and 'output' in entry:
            txt_file.write(f"{entry['input']}\t{entry['output']}\n")

print(f'Data from {input_json_file} has been extracted to {output_txt_file} with tabs.')
