import os
import re
from pathlib import Path

ROOT_DIR = Path("blueprint")
STATIC_PATH_PATTERN = re.compile(r'static_folder\s*=\s*r?[\'"](/home/ec2-user/Stock-Scanner-Project/static)[\'"]')
BASEDIR_PATTERN = re.compile(r'BASE_DIR\s*=\s*r?[\'"](/home/ec2-user/Stock-Scanner-Project/)[\'"]')
ROUTE_PATTERN = re.compile(r'^\s*@app\.route', re.MULTILINE)

def fix_flask_file(path: Path):
    with path.open("r") as f:
        content = f.read()

    # Update static folder paths
    content = STATIC_PATH_PATTERN.sub(
        'static_folder=str((Path(__file__).parent.parent / "static").resolve())', content
    )
    # Update BASE_DIR
    content = BASEDIR_PATTERN.sub(
        'BASE_DIR = str((Path(__file__).parent.parent).resolve())', content
    )

    # Ensure `from pathlib import Path` exists
    if "from pathlib import Path" not in content:
        content = "from pathlib import Path\n" + content

    # Ensure Flask is imported before app = Flask(...)
    if "from flask import Flask" not in content:
        content = "from flask import Flask\n" + content

    # Move `app = Flask(...)` above all `@app.route` lines
    match = ROUTE_PATTERN.search(content)
    if match:
        app_def = re.search(r'app\s*=\s*Flask\([^)]+\)', content)
        if app_def and app_def.start() > match.start():
            app_line = app_def.group(0)
            content = content.replace(app_line, '')
            insert_at = match.start()
            content = content[:insert_at] + app_line + '\n' + content[insert_at:]

    with path.open("w") as f:
        f.write(content)
    print(f"✅ Fixed: {path}")

def main():
    flask_files = list(ROOT_DIR.rglob("*.flask.py"))
    for file in flask_files:
        fix_flask_file(file)

if __name__ == "__main__":
    main()
