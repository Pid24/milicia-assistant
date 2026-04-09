import os
import sys

def create_startup_script():
    # Mendapatkan path absolut ke folder virtual environment dan file milicia.py
    project_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(project_dir, "venv", "Scripts", "pythonw.exe") # Gunakan pythonw.exe agar tidak ada window CMD
    script_path = os.path.join(project_dir, "milicia.py")
    
    # Path ke folder Startup Windows
    startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    vbs_path = os.path.join(startup_dir, "MiliciaAutoStart.vbs")
    
    # Isi file VBScript untuk menjalankan perintah secara hidden (0 = vbHide)
    vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "{python_exe}" & chr(34) & " " & chr(34) & "{script_path}" & chr(34) & " --background", 0
Set WshShell = Nothing
"""

    try:
        with open(vbs_path, "w") as f:
            f.write(vbs_content)
        print(f"Sukses! Shortcut startup telah dibuat di:\n{vbs_path}")
        print("Mulai sekarang, Milicia akan jalan menyapa tanpa terlihat saat Windows dinyalakan.")
    except Exception as e:
        print(f"Gagal membuat autostart: {e}")

if __name__ == "__main__":
    create_startup_script()
