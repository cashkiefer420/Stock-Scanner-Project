import os
import re

BASE_DIR = "blueprint"
PATCH_STRING = '''import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, "..", "..", "static")
JSON_FOLDER = os.path.join(BASE_DIR, "..", "..", "json")
os.makedirs(JSON_FOLDER, exist_ok=True)
'''

def patch_file(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        # Remove any hardcoded EC2 paths
        if "/home/ec2-user/Stock-Scanner-Project" in line:
            modified = True
            continue
        new_lines.append(line)

    if modified:
        print(f"⚙️  Patching {file_path}")
        # Insert the patch at the top
        new_content = PATCH_STRING + "\n" + "".join(new_lines)
        with open(file_path, "w") as f:
            f.write(new_content)

def main():
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".py"):
                patch_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
