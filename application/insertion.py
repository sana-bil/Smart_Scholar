import csv

input_file = r'C:\Users\Home\Documents\Projects\Smart Scholar\dataset.txt'
output_file = r'C:\Users\Home\Documents\Projects\Smart Scholar\dataset_clean.txt'

# Columns to REMOVE (0-based index)
columns_to_remove = [3, 4]  # duration_months, ects_credits

with open(input_file, mode='r', encoding='utf-8-sig') as infile, \
     open(output_file, mode='w', encoding='utf-8', newline='') as outfile:

    reader = csv.reader(infile, delimiter=',', quotechar='"')
    writer = csv.writer(outfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        row = [col for idx, col in enumerate(row) if idx not in columns_to_remove]
        writer.writerow(row)

print("CSV cleaned and ready for import:", output_file)
