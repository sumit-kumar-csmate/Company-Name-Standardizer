import sys
sys.path.insert(0, '.')
from app import process_single_name
from company_normalizer.core.merge_engine import can_merge

n1 = process_single_name("Avia Avian")
n2 = process_single_name("Avia Avian Tbk")

print("=== Name 1 ===")
print("Base:", repr(n1.get('base_name')))
print("Suffix:", repr(n1.get('legal_suffix')))
print("Family:", repr(n1.get('legal_family')))
print("Cleaned:", repr(n1.get('cleaned_upper')))

print("\n=== Name 2 ===")
print("Base:", repr(n2.get('base_name')))
print("Suffix:", repr(n2.get('legal_suffix')))
print("Family:", repr(n2.get('legal_family')))
print("Cleaned:", repr(n2.get('cleaned_upper')))

ok, reason = can_merge(n1, n2, set())
print("\nCan merge?", ok, reason)
