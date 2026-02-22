import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ViewSets are ONLY allowed in these paths
ALLOWED_VIEWSET_PATHS = (
    os.sep + "views",
    "viewsets.py",
)

# These files must NEVER import ViewSets
FORBIDDEN_VIEWSET_IMPORT_LOCATIONS = (
    "models.py",
    "serializers.py",
    os.sep + "services",
)

IGNORE_DIRS = {
    "venv",
    "__pycache__",
    "migrations",
    "node_modules",
    ".git",
    "tools",
}


def should_ignore(path):
    return any(d in path for d in IGNORE_DIRS)


def is_viewset_file(path):
    return any(p in path for p in ALLOWED_VIEWSET_PATHS)


def scan_file(filepath):
    findings = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for lineno, line in enumerate(f, start=1):
            if "ViewSet" in line or "viewsets." in line:
                findings.append((lineno, line.strip()))
    return findings


def main():
    print("\n🔍 Django STRUCTURE VERIFICATION (SMART MODE)\n")
    issues = []

    for root, _, files in os.walk(BASE_DIR):
        if should_ignore(root):
            continue

        for file in files:
            if not file.endswith(".py"):
                continue

            path = os.path.join(root, file)

            if is_viewset_file(path):
                continue  # allowed

            if any(bad in path for bad in FORBIDDEN_VIEWSET_IMPORT_LOCATIONS):
                findings = scan_file(path)
                if findings:
                    issues.append((path, findings))

    if not issues:
        print("✅ Structure clean. No illegal ViewSet imports.\n")
        return

    print("❌ ILLEGAL ViewSet Imports Found:\n")
    for path, findings in issues:
        print(f"📄 {path}")
        for lineno, content in findings:
            print(f"   ⚠ Line {lineno}: {content}")
        print()

    print("🚨 These WILL break Django model registry.\n")


if __name__ == "__main__":
    main()
