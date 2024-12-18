from cx_Freeze import setup, Executable
import os

def include_files(source_folder, target_folder):
    files = []
    try:
        for root, _, filenames in os.walk(source_folder):
            for filename in filenames:
                source_path = os.path.join(root, filename)
                relative_path = os.path.relpath(source_path, source_folder)
                target_path = os.path.join(target_folder, relative_path)
                files.append((source_path, target_path))
    except Exception as e:
        print(f"Error processing files: {e}")
        return []
    return files

# Define specific files to include
additional_files = [
    ("data/main.py", "lib/main.py"),
    ("data/variables.py", "lib/variables.py"),
] + include_files("data/img", "lib/img/")

executables = [
    Executable(
        script="data/main.py",
        base="Win32GUI", 
        target_name="SourceViewer.exe",
        icon="data/img/icon.ico"
    )
]

setup(
    name="SourceViewer",
    version="1.2.0",
    description="Source Viewer Application",
    options={
        "build_exe": {
            "include_msvcr": True,
            "packages": [
                "tkinter",
                "cv2",
                "numpy",
                "pyaudio",
                "customtkinter",
                "pygrabber",
                "requests",
                "ffmpegcv",
                "pygame",
                "comtypes.stream"
            ],
            "excludes": ["pytest"],
            "include_files": additional_files,
            "build_exe": "output-build"
        }
    },
    executables=executables
)