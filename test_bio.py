import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('app.py')))

# Use EXACTLY the same pipeline as process_single_name in app.py
from company_normalizer.processors.text_cleaner import clean_text
from company_normalizer.processors.address_remover import remove_address_details
from company_normalizer.processors.prefix_remover import remove_prefixes
from company_normalizer.processors.legal_suffix_normalizer import extract_and_normalize_suffix
from company_normalizer.processors.descriptor_checker import extract_descriptors
from company_normalizer.processors.geographic_matcher import extract_geography
from company_normalizer.core.merge_engine import build_merge_groups, _names_differ_only_by_spaces
from company_normalizer.core.canonical_generator import generate_canonical_for_group, format_canonical_name

def process_single_name(raw_name):
    cleaned_display, cleaned_upper = clean_text(raw_name)
    no_address, removed_address = remove_address_details(cleaned_upper)
    no_prefix, removed_prefixes = remove_prefixes(no_address)
    base_name, legal_suffix, legal_family = extract_and_normalize_suffix(no_prefix)
    return {
        'original': raw_name, 'cleaned': cleaned_display, 'cleaned_upper': cleaned_upper,
        'removed_address': removed_address, 'removed_prefixes': removed_prefixes,
        'base_name': base_name, 'legal_suffix': legal_suffix, 'legal_family': legal_family,
        'descriptors': extract_descriptors(base_name),
        'geography': extract_geography(base_name),
    }

names = [
    'JILIN COFCO BIO-CHEM & BIOENERGY MARKETING CO.,LTD.',
    'JILIN COFCO BIO-CHEM & BIO-ENERGY MARKETING CO.,LTD.',
    'JILIN COFCO BIO CHEM & BIO ENERGY MARKETING CO.,LTD.',
    'JILIN COFCO BIO-CHEM & BIO ENERGY MARKETING CO.,LTD.',
    'JILIN COFCO BIO-CHEM & BIO - ENERGY MARKETING CO.,LTD.',
]

name_data = [process_single_name(n) for n in names]

with open('c:/tmp/app_trace.txt', 'w', encoding='utf-8') as f:
    f.write("=== INTERMEDIATE STATE ===\n")
    for i, nd in enumerate(name_data):
        f.write(f"[{i}] orig:    {nd['original']}\n")
        f.write(f"    cleaned: {nd['cleaned_upper']}\n")
        f.write(f"    no_addr: {nd['removed_address']}\n")
        f.write(f"    no_pfx:  {nd['removed_prefixes']}\n")
        f.write(f"    base:    {nd['base_name']}\n")
        f.write(f"    suffix:  {nd['legal_suffix']}  family: {nd['legal_family']}\n")
        f.write(f"    desc:    {nd['descriptors']}\n")
        f.write(f"    geo:     {nd['geography']}\n\n")

    f.write("=== SPACE_ONLY CHECKS ===\n")
    for i in range(len(name_data)):
        for j in range(i+1, len(name_data)):
            b1 = name_data[i]['base_name']
            b2 = name_data[j]['base_name']
            chk = _names_differ_only_by_spaces(b1, b2)
            if chk:
                f.write(f"[{i}] vs [{j}] SPACE_ONLY triggered!\n")

    groups = build_merge_groups(name_data)
    f.write(f"\n=== GROUPS ({len(groups)} total) ===\n")
    for g in groups:
        idxs = g['indices']
        reason = g['merge_reason']
        canon = format_canonical_name(generate_canonical_for_group(name_data, idxs, reason))
        f.write(f"Group {idxs}  reason={reason}\n  → {canon}\n")

print("Written to c:/tmp/app_trace.txt")
