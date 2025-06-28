import json
import time
import threading
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed

# CONFIG
API_KEY = "AIzaSyC4cSOxwjAp9fIVKW9bdOcszNWBiQzjg4k"
INPUT_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/final_caste_1/output/caste_structure_final_with_uid copy.json"

OUTPUT_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/final_caste_1/output/caste_structure_final_transliterated_new_copy.json"
# FAILED_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/final_caste_1/output/caste_failed.json"
# UNCHANGED_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/final_caste_1/output/caste_unchanged.json"

# Gemini setup
genai.configure(api_key="AIzaSyC4cSOxwjAp9fIVKW9bdOcszNWBiQzjg4k")
model = genai.GenerativeModel("gemini-2.0-flash")

lang_map = {
    "Hi": "Hindi", "As": "Assamese", "Bn": "Bengali", "Gu": "Gujarati",
    "Kn": "Kannada", "Ml": "Malayalam", "Mr": "Marathi", "Or": "Odia",
    "Pa": "Punjabi", "Ta": "Tamil", "Te": "Telugu"
}


# Thread-safe result containers
lock = threading.Lock()
success_list = []
failed_list = []
unchanged_list = []

# Load data
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
# data = data[:10]
# Build strict clean prompt
def build_prompt(name):
    return f"""
You are a strict transliteration engine for Indian caste and sub-caste names.

Transliterate the word "{name}" into the following Indian languages:
Hindi (Hi), Assamese (As), Bengali (Bn), Gujarati (Gu), Kannada (Kn), Malayalam (Ml), Marathi (Mr), Odia (Or), Punjabi (Pa), Tamil (Ta), Telugu (Te).

⚠️ Strict Instructions:
- Only output the word in **native script** of each language.
- Do **not** include transliteration in English or Latin/Roman letters.
- Do **not** use phonetic approximations — use proper script-based transliteration.
- Do **not** add any explanation, language label, punctuation, brackets, or formatting (like *, |, () or diacritics).
- The output should be **clean, plain**, and directly usable as display text.
- The term may be a compound caste name; transliterate it as a **proper noun**, with correct casing and spacing.

Respond in **exactly** this format:
Hi: [native script only]  
As: [native script only]  
Bn: [native script only]  
Gu: [native script only]  
Kn: [native script only]  
Ml: [native script only]  
Mr: [native script only]  
Or: [native script only]  
Pa: [native script only]  
Ta: [native script only]  
Te: [native script only]
"""

# Parse response like: "Hi: अब्बासी\nBn: আব্বাসী\n..."
def parse_response(text):
    result = {}
    lines = text.strip().splitlines()
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key in lang_map:
                result[key] = val
    return result

def process_entry(caste):
    name = caste["name"].strip().upper()
    original_display = caste.get("displayName", {}).copy()
    prompt = build_prompt(name)

    try:
        response = model.generate_content(prompt)
        print(response.text)
        parsed = parse_response(response.text)

        # If parsed successfully, update displayName
        caste["displayName"].update(parsed)

        changed = any(caste["displayName"].get(k, "") != original_display.get(k, "") for k in lang_map)

        with lock:
            if changed:
                success_list.append(caste)
                print(f"✅ {name}")
            else:
                unchanged_list.append(caste)
                print(f"⚠️  {name} (unchanged)")
    except Exception as e:
        with lock:
            caste["error"] = str(e)
            failed_list.append(caste)
            print(f"❌ {name} (error)")

# Run with threading
start_time = time.time()

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_entry, caste) for caste in data]
    for _ in as_completed(futures):
        pass

# Save files
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(success_list, f, ensure_ascii=False, indent=2)

# with open(FAILED_FILE, "w", encoding="utf-8") as f:
#     json.dump(failed_list, f, ensure_ascii=False, indent=2)

# with open(UNCHANGED_FILE, "w", encoding="utf-8") as f:
#     json.dump(unchanged_list, f, ensure_ascii=False, indent=2)

# Summary
elapsed = round(time.time() - start_time, 2)
print(f"\n✅ Done in {elapsed}s")
print(f"  🟢 Success    : {len(success_list)}")
print(f"  ⚠️  Unchanged : {len(unchanged_list)}")
print(f"  🔴 Failed     : {len(failed_list)}")
print(f"\nFiles saved:\n  {OUTPUT_FILE}\n  {UNCHANGED_FILE}\n  {FAILED_FILE}")