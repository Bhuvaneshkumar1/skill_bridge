import os
import sys
from pathlib import Path

# Find project root directory
project_root = Path(__file__).resolve().parent.parent

# Add project root to sys.path and PYTHONPATH
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root) + os.pathsep + os.environ.get("PYTHONPATH", "")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Launching SkillBridge AI Backend from: {project_root}")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
