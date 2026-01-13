
import json

with open("debug_dynamics_new.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Loaded {len(data)} items.")

found_additional = False
for item in data:
    modules = item.get("modules", {})
    module_dynamic = modules.get("module_dynamic", {})
    additional = module_dynamic.get("additional")
    
    if additional:
        found_additional = True
        print(f"Found additional data in item {item.get('id_str')}:")
        print(json.dumps(additional, ensure_ascii=False, indent=2))
        
if not found_additional:
    print("No 'additional' data found in any items.")
