import pandas as pd
df = pd.read_csv('test_rules_output.csv')
for i, r in df.iterrows():
    print(f"{i:2}. {r['Importer Name'][:35]:35} -> {r['Standardised Name'][:35]:35} ({r['Confidence Score']}) | SS: {r['Subset Highlight']} | ND: {r['Near Dup Highlight']} | Review: {r['Review Flag']}")
