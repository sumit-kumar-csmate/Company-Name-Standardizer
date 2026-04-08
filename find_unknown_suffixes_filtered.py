import sys
sys.path.insert(0, '.')
import pandas as pd
from collections import Counter
from app import process_single_name
from company_normalizer.config.legal_suffixes import get_all_suffixes

csv_path = r"C:\Users\Admin\Downloads\Cleaning Tool 2.0\Cleaning Tool 2.0 (Sumit Changes)\Total name.csv"

# Build blacklists
known_suffixes = set([s.upper() for s in get_all_suffixes()])
# add "LIMITED", "CO", "COMPANY", "PRIVATE" just in case they slipped through
known_suffixes.update(["LIMITED", "CO", "COMPANY", "PRIVATE", "PVT", "LTD", "PLC", "INC", "CORP", "CORPORATION"])

common_business_words = set([
    "CHEMICAL", "CHEMICALS", "CHEM", "INDUSTRY", "INDUSTRIES", "INDUSTRIAL", 
    "TRADING", "TRADERS", "TRADE", "ENTERPRISE", "ENTERPRISES", 
    "GROUP", "TECHNOLOGY", "TECHNOLOGIES", "TECH", 
    "PRODUCTS", "SERVICES", "EXPORT", "EXPORTS", "IMPORT", "IMPORTS", "IMPEX", 
    "PHARMA", "PHARMACEUTICALS", "INGREDIENTS", "MATERIAL", "MATERIALS", 
    "MANUFACTURING", "MANUFACTURERS", "FOODS", "FOOD", "LABORATORIES", "GLOBAL", 
    "SOLUTIONS", "TEXTILES", "TEXTILE", "BROTHERS", "SONS",
    "QUIMICA", "QUIMICOS", "COMERCIO", "LOGISTICS", "INTERNATIONAL", "INTL",
    "JAYA", "ABADI", "MANDIRI", "MAKMUR", "SENTOSA", "ALAM", "INDAH" # Indonesian common words
])

try:
    df = pd.read_csv(csv_path)
    col_name = df.columns[0]
    
    last_words = []
    
    for val in df[col_name]:
        if pd.isna(val): continue
        name = str(val).strip()
        res = process_single_name(name)
        
        base = res.get('base_name', '')
        geos = set(res.get('geography', []))
        
        if base:
            tokens = base.split()
            if tokens:
                last_w = tokens[-1].upper()
                if len(last_w) > 1 and last_w not in known_suffixes and last_w not in common_business_words and last_w not in geos:
                    last_words.append(last_w)
                
    c = Counter(last_words)
    
    with open('unknown_suffixes.txt', 'w', encoding='utf-8') as f:
        f.write("--- FILTERED MOST COMMON UNKNOWN TRAILING WORDS ---\n")
        f.write("Potentially missing legal suffixes:\n\n")
        for word, count in c.most_common(50):
            f.write(f"{word:<20} : {count}\n")
    print("Done writing filtered output.")
except Exception as e:
    print("Error:", e)
