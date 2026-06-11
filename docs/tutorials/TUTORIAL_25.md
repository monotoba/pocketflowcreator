# Tutorial 25: Packaging for Distribution

**What you'll learn:** Use the PyInstaller spec files to create a self-contained executable.

### Steps

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build for Linux:
   ```bash
   bash scripts/package.sh linux
   ```
   Output: `dist/pocketflow-creator` (single executable)

3. Build for Windows (on a Windows host):
   ```bash
   bash scripts/package.sh windows
   ```
   Output: `dist/pocketflow-creator.exe`

4. Share the executable — no Python installation required on the target machine

---
