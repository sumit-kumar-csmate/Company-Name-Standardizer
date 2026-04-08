import os
import pandas as pd
from dotenv import load_dotenv
from app import process_dataframe

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 1. Define Comprehensive Test Cases
test_data = {
    "Importer Name": [
        "M/S Tata Chemical Magadhi Ltd.",            # Prefix + Singular + Ltd
        "Tata Magadhi Chemicals Limited",           # Proper + Plural + Limited
        "Samsung Electronics Pvt Ltd",               # Pvt Ltd
        "Samsung Electronics Private Limited",       # Private Limited
        "ABC Corp. Building 5, Floor 3",             # Address details
        "Chemicals Tata",                            # Word order
        "BEST CARE SOLUTIONS & FAYSAL BANK",         # AI: Bank stripping (Rule 73)
        "BEST CARE SOLUTIONS = NTN A801561-3",       # AI: NTN stripping (Rule 73)
        "COFOC",                                     # AI: Near-duplicate spelling
        "COFCO",                                     # AI: Near-duplicate spelling
        "BIO ENERGY",                                # Subset check
        "BIO ENERGY PVT LTD",                        # Subset check
        "Alpha & Beta",                              # & -> And
    ]
}

df_test = pd.DataFrame(test_data)

print(f"🚀 Starting Comprehensive test of {len(df_test)} cases...")

if not api_key:
    print("⚠️ WARNING: No API Key found in .env. AI tests will be skipped/fall back to rules.")

# 2. Run the process_dataframe logic (Stage 1 to 6)
# Use a specific model to ensure consistent results for testing
try:
    result_df, total, n_groups, ai_status, near_dup_canons = process_dataframe(
        df_test, 
        "Importer Name", 
        api_key=api_key, 
        model_name="gemini-2.5-flash"
    )

    print(f"\n✅ Processing Complete!")
    print(f"📊 Total Rows: {total}")
    print(f"📊 Groups formed: {n_groups}")
    print(f"🤖 AI Status: {ai_status}")

    # 3. Output results for verification
    cols_to_show = ["Importer Name", "Standardised Name", "Confidence Score", "Review Flag", "Subset Highlight", "Near Dup Highlight"]
    print("\n--- TEST RESULTS ---")
    
    # Format the print for clarity
    for _, row in result_df.iterrows():
        print(f"Original: {row['Importer Name']}")
        print(f"Standardised: {row['Standardised Name']}")
        print(f"Confidence: {row['Confidence Score']} | Review: {row['Review Flag']}")
        if row.get('Subset Highlight'): print("🟡 Highlight: SUBSET")
        if row.get('Near Dup Highlight'): print("🔵 Highlight: NEAR-DUP (Tiffany Blue)")
        print("-" * 30)

    # 4. Save to CSV for in-depth inspection
    result_df.to_csv("test_rules_output.csv", index=False)
    print("\n💾 Detailed results saved to 'test_rules_output.csv'")

except Exception as e:
    print(f"❌ Error during test execution: {e}")
    import traceback
    traceback.print_exc()
