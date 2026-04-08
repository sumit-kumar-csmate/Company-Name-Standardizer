import collections
import re

counts = collections.Counter()
pattern = re.compile(r'^(TO THE ORDER(?: OF)?|TO ORDER(?: OF)?|ON ORDER(?: OF)?|ORDER OF)', re.IGNORECASE)

try:
    with open('Total name.csv', 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip().strip('\"\'')
            words = line.upper().split()
            prefix = ' '.join(words[:5])
            if 'ORDER' in prefix:
                counts[prefix] += 1
                
except Exception as e:
    print(e)
    
print('Top ORDER variations:')
for k, v in counts.most_common(100):
    if k.startswith('TO') or k.startswith('ORDER'):
        print(f'{k}: {v}')
