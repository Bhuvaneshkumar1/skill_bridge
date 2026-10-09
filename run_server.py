import os
import sys
from pathlib import Path

# Find project root directory (directory containing backend/)
current_dir = Path(__file__).resolve().parent
if (current_dir / "backend").exists():
    project_root = current_dir
elif (current_dir.parent / "backend").exists():
    project_root = current_dir.parent
else:
    project_root = current_dir

# Add project root to sys.path and PYTHONPATH
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root) + os.pathsep + os.environ.get("PYTHONPATH", "")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Launching SkillBridge AI Backend from: {project_root}")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
