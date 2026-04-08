import sys
sys.path.insert(0, '.')
import pandas as pd
from collections import Counter
from app import process_single_name

csv_path = r"C:\Users\Admin\Downloads\Cleaning Tool 2.0\Cleaning Tool 2.0 (Sumit Changes)\Total name.csv"

try:
    df = pd.read_csv(csv_path)
    col_name = df.columns[0]
    
    last_words = []
    
    for val in df[col_name]:
        if pd.isna(val): continue
        name = str(val).strip()
        res = process_single_name(name)
        
        base = res.get('base_name', '')
        if base:
            tokens = base.split()
            if tokens:
                last_words.append(tokens[-1])
                
    c = Counter(last_words)
    
    with open('unknown_suffixes.txt', 'w') as f:
        f.write("--- MOST COMMON LAST WORDS (Potential Suffixes) ---\n")
        for word, count in c.most_common(60):
            f.write(f"{word:<20} : {count}\n")
        print("Done writing to unknown_suffixes.txt")
except Exception as e:
    print("Error:", e)
