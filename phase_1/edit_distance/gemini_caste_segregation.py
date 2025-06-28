import pandas as pd
import time
from tqdm import tqdm
import google.generativeai as genai
import json

# Initialize Gemini with your API key
genai.configure(api_key="")
model = genai.GenerativeModel("gemini-1.5-flash-8b-001")

# Load the caste-state data
df = pd.read_csv("not_matched_castes_all_states.csv")
df = df[26:30]

import json

def classify_keyword_with_gemini(keyword):
    prompt = f"""
You are a caste classification assistant trained on Indian community data.

You will be given a **community keyword** that may refer to a caste, sub-caste, tribe, or sub-tribe in India.

### TASK:
1. Determine if the keyword is a "caste", "sub-caste", "tribe", "sub-tribe", or "unknown".
2. If it is a **sub-caste** or **sub-tribe**, identify its **parent caste or tribe**. Record that parent in the "caste" field.
   - Treat all **sub-tribes as sub-castes** and record their parent tribe as the **caste**.
3. If it is a **caste** or **tribe**, copy it to the "caste" field.
4. If you’re not confident or cannot find factual evidence, return "unknown" and "NA".

✅ Use factual Indian classification from constitutional, anthropological, or regional official sources only.

Return output strictly in this JSON format:
{{
  "type": "caste" | "sub-caste" | "tribe" | "sub-tribe" | "unknown",
  "caste": "..."  // parent caste/tribe for sub-*, "NA" if unknown
}}

Classify the keyword: {keyword}
"""
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()

        # Strip code block if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()

        print(f"\n📥 Gemini Cleaned Response:\n{content}")

        result = json.loads(content)
        if "type" not in result or "caste" not in result:
            raise ValueError("Missing required keys in JSON")
        return result

    except Exception as e:
        print(f"❌ Error for {state} - {keyword}: {e}")
        return {
            "type": "unknown",
            "caste": "NA"
        }

# Collect results
results = []

for _, row in tqdm(df.iterrows(), total=len(df)):
    state = row["State"]
    keyword = row["keywords"]
    result = classify_keyword_with_gemini(keyword)
    results.append({
        "State_UT": state,
        "Keyword": keyword,
        "Type": result["type"],
        "Caste": result["caste"]
    })
    time.sleep(1.5)  # delay to avoid API rate limits

# Save to CSV
output_df = pd.DataFrame(results)
output_df.to_csv("classified_keywords_by_gemini_2.csv", index=False)

print("✅ Gemini output saved to 'classified_keywords_by_gemini.csv'")