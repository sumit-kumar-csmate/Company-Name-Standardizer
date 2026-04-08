import os
import pandas as pd
from dotenv import load_dotenv
from app import process_dataframe

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

FILE_PATH = "test.xlsx"
COL_NAME = "Importer Name"

if not os.path.exists(FILE_PATH):
    print(f"❌ Error: {FILE_PATH} not found.")
    exit(1)

# Read the file
print(f"📂 Loading {FILE_PATH}...")
df_test = pd.read_excel(FILE_PATH)

if COL_NAME not in df_test.columns:
    print(f"❌ Error: Column '{COL_NAME}' not found. Found columns: {df_test.columns.tolist()}")
    exit(1)

print(f"🚀 Processing {len(df_test)} rows...")

# Run the process_dataframe logic
try:
    result_df, total, n_groups, ai_status, near_dup_canons = process_dataframe(
        df_test, 
        COL_NAME, 
        api_key=api_key, 
        model_name="gemini-2.5-flash"
    )

    print(f"\n✅ Processing Complete!")
    print(f"📊 Total Rows: {total}")
    print(f"📊 Groups formed: {n_groups}")
    print(f"🤖 AI Status: {ai_status}")

    # Output top changes and suspicious groups
    print("\n--- SAMPLE TRANSFORMATIONS ---")
    changed = result_df[result_df[COL_NAME].str.lower() != result_df["Standardised Name"].str.lower()]
    print(f"Found {len(changed)} transformations.")
    
    # Save results to a preview format
    preview = changed[[COL_NAME, "Standardised Name", "Confidence Score", "Review Flag"]].head(30)
    print(preview.to_string())

    # Save to CSV
    result_df.to_csv("test_results_full.csv", index=False)
    print("\n💾 Full results saved to 'test_results_full.csv'")

except Exception as e:
    print(f"❌ Error during execution: {e}")
    import traceback
    traceback.print_exc()
