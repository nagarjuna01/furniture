import os
import sys
import ast
import django
from pathlib import Path

# --- AUTO-CONFIG ---
APP_NAME = "modular_calc"

def find_settings():
    """Attempts to find the Django settings module automatically."""
    for path in Path('.').rglob('settings.py'):
        if 'venv' not in str(path) and 'env' not in str(path):
            return str(path.parent).replace(os.sep, '.')
    return None

PROJECT_SETTINGS = find_settings()

# --- DJANGO SETUP ---
sys.path.append(os.getcwd())
if PROJECT_SETTINGS:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{PROJECT_SETTINGS}.settings')
    try:
        django.setup()
        from django.apps import apps
        HAS_DJANGO = True
    except Exception as e:
        print(f"⚠️ Django setup failed: {e}")
        HAS_DJANGO = False
else:
    print("⚠️ Could not find a folder containing settings.py. Skipping DB checks.")
    HAS_DJANGO = False

def deep_search_models(app_name):
    """Checks the database for models defined in this app."""
    if not HAS_DJANGO: return
    
    print(f"\n--- 🔍 DEEP SEARCH: DATABASE STATE ---")
    try:
        app_config = apps.get_app_config(app_name)
        # Use simple sorting to keep output clean
        sorted_models = sorted(app_config.models.items(), key=lambda x: x[0])
        for model_name, model in sorted_models:
            try:
                count = model.objects.count()
                print(f"✅ {model.__name__:<25} | Records: {count}")
            except Exception:
                print(f"❌ {model.__name__:<25} | Table missing or migration pending")
    except Exception as e:
        print(f"❌ Error accessing app models: {e}")

def analyze_logic_dependencies(app_path):
    """Analyzes if views are correctly importing from the evaluation engine."""
    print(f"\n--- 🧠 DEEP SEARCH: LOGIC DEPENDENCIES ---")
    view_path = os.path.join(app_path, "views.py")
    
    # We look for references to either the class or the evaluation module
    if os.path.exists(view_path):
        try:
            # Force UTF-8 to avoid UnicodeDecodeError on Windows
            with open(view_path, "r", encoding="utf-8") as f:
                content = f.read()
                found_engine = "ProductEngine" in content or "evaluation" in content
                if found_engine:
                    print("✅ Integration: Views are referencing the Evaluation Engine.")
                else:
                    print("⚠️ Warning: Views do not seem to reference ProductEngine or the evaluation module.")
        except Exception as e:
            print(f"❌ Error reading views.py: {e}")

def list_structure(app_name: str):
    app_path = os.path.join(os.getcwd(), app_name)
    if not os.path.exists(app_path):
        print(f"App folder '{app_name}' not found!")
        return

    # 1. Database Check
    deep_search_models(app_name)
    
    # 2. Logic Integrity Check
    analyze_logic_dependencies(app_path)

    # 3. Code Map
    print(f"\n--- 📂 ARCHITECTURE MAP: {app_name} ---")
    for root, dirs, files in os.walk(app_path):
        if any(x in root for x in ['migrations', '__pycache__', 'env', 'venv']):
            continue
        
        py_files = [f for f in files if f.endswith(".py")]
        for f in py_files:
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path, app_path)
            print(f"📄 {rel_path}")
            
            try:
                # Force UTF-8 here as well for the AST parser
                with open(file_path, "r", encoding="utf-8") as file:
                    tree = ast.parse(file.read())
                    for node in ast.iter_child_nodes(tree):
                        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                            prefix = "  🔹 Class" if isinstance(node, ast.ClassDef) else "  🔸 Func"
                            print(f"    {prefix}: {node.name}")
            except Exception as e:
                # Silent skip for parsing errors, just move to next file
                continue
            print()

if __name__ == "__main__":
    list_structure(APP_NAME)