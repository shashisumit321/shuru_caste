# import json
# import os
# from multiprocessing import Pool, cpu_count, Manager
# from deep_translator import GoogleTranslator

# INPUT_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/caste_structure_base.json"
# OUTPUT_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/output/caste_structure_final_transliterated.json"
# LANGUAGES = ["en", "hi", "as", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te"]

# # ✅ MUST be top-level
# def translate_entry(entry):
#     name = entry['name']
#     display_name = {}

#     for lang in LANGUAGES:
#         try:
#             translated = GoogleTranslator(source='en', target=lang).translate(name)
#             display_name[lang.capitalize()] = translated
#         except Exception:
#             display_name[lang.capitalize()] = name

#     entry['displayName'] = display_name
#     return entry

# def listener(queue, total):
#     completed = 0
#     while completed < total:
#         queue.get()
#         completed += 1
#         print(f"✅ Translated: {completed}/{total}", end="\r")

# def worker_wrapper(args):
#     entry, queue = args
#     result = translate_entry(entry)
#     queue.put(1)
#     return result

# def main():
#     if not os.path.exists(INPUT_FILE):
#         print(f"❌ Input file not found: {INPUT_FILE}")
#         return

#     with open(INPUT_FILE, "r", encoding="utf-8") as f:
#         data = json.load(f)
#         # data = data[:22]  # Remove limit in full run

#     os.makedirs("output", exist_ok=True)
#     num_processes = min(cpu_count(), 12)

#     print(f"⚙️ Translating {len(data)} entries with {num_processes} workers...")

#     with Manager() as manager:
#         queue = manager.Queue()
#         pool = Pool(processes=num_processes)

#         # Start listener process
#         from threading import Thread
#         t = Thread(target=listener, args=(queue, len(data)))
#         t.start()

#         results = pool.map(worker_wrapper, [(entry, queue) for entry in data])

#         t.join()
#         pool.close()
#         pool.join()

#         with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#             json.dump(results, f, indent=2, ensure_ascii=False)

#     print(f"\n🎉 Done! Output saved to: {OUTPUT_FILE}")

# if __name__ == "__main__":
#     main()



import json
import os
from multiprocessing import Pool, cpu_count, Manager
from google.cloud import translate_v2 as translate
import google.auth

# Set your Google credentials environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/shashiranjan/keys/gcloud-translate-key.json"

INPUT_FILE = "/Users/shashiranjan/Desktop/shuru/location_heirarchy_list/caste_data/phase_2/json_output_formate/caste_structure_base.json"
OUTPUT_FILE = "output/caste_structure_final_transliterated_google.json"
LANGUAGES = ["en", "hi", "as", "bn", "gu", "kn", "ml", "mr", "or", "pa", "ta", "te"]

# Must be defined globally for multiprocessing
def translate_entry(entry):
    client = translate.Client()
    name = entry['name']
    display_name = {}

    for lang in LANGUAGES:
        try:
            result = client.translate(name, source_language='en', target_language=lang)
            display_name[lang.capitalize()] = result['translatedText']
        except Exception:
            display_name[lang.capitalize()] = name

    entry['displayName'] = display_name
    return entry

def listener(queue, total):
    completed = 0
    while completed < total:
        queue.get()
        completed += 1
        print(f"✅ Translated: {completed}/{total}", end="\r")

def worker_wrapper(args):
    entry, queue = args
    result = translate_entry(entry)
    queue.put(1)
    return result

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs("output", exist_ok=True)
    num_processes = min(cpu_count(), 10)

    print(f"⚙️ Translating {len(data)} entries with {num_processes} workers...")

    with Manager() as manager:
        queue = manager.Queue()
        pool = Pool(processes=num_processes)

        from threading import Thread
        t = Thread(target=listener, args=(queue, len(data)))
        t.start()

        results = pool.map(worker_wrapper, [(entry, queue) for entry in data])

        t.join()
        pool.close()
        pool.join()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Done! Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()