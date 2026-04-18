import csv

input_file = "train.tsv"
output_file = "data/data.txt"

def convert_label_to_fact(claim, label):
    claim = claim.strip()

    # Simple rule-based conversion
    if label in ["false", "pants-fire", "barely-true"]:
        return "It is false that " + claim
    elif label in ["true", "mostly-true"]:
        return claim
    else:
        return None  # skip uncertain

with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
    reader = csv.reader(f, delimiter="\t")

    for row in reader:
        if len(row) < 2:
            continue

        label = row[1].lower()
        claim = row[2]

        fact = convert_label_to_fact(claim, label)

        if fact:
            out.write(fact + "\n")

print("✅ Data converted successfully!")