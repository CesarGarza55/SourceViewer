# SourceViewer

**SourceViewer** is a Python application built using `customtkinter` that allows you to visualize video and audio sources connected to your computer. The application provides an easy-to-use interface to select, view, and listen to your media sources.

It is possible that some device is not listed in the application, if so please report it and I will try to add it to the listed devices, this is because in Windows there are dozens of devices and the pyaudio library detects all of them, although not all of them are usable devices.

This project was born from the small number of applications that allow you to view inputs from video capture devices or cameras without the need for applications like OBS that usually consume too many resources, for people who do not need to record their screen this app will allow you to only view it.

## Features

- **Video Source Selection**: Detect and select from available video input devices.
- **Audio Source Selection**: Detect and select from available audio input devices.
- **Fullscreen Mode**: View video sources in fullscreen mode.
- **Download Latest Version**: Automatic detection of updates with the option to download the latest release.

## Requirements

- Python 3.12.x
- [OpenCV](https://pypi.org/project/opencv-python/)
- [Pillow](https://pypi.org/project/Pillow/)
- [pyaudio](https://pypi.org/project/PyAudio/)
- [requests](https://pypi.org/project/requests/)
- [customtkinter](https://pypi.org/project/customtkinter/)
- [pygrabber](https://pypi.org/project/pygrabber/)

## Compile

1. Clone the repository:
   ```sh
   git clone https://github.com/CesarGarza55/SourceViewer.git
   cd SourceViewer
   ```

2. Install the required dependencies:
   ```sh
   pip install -r data/requirements.txt
   ```

3. Compile:
   ```sh
   pyinstaller --clean --workpath ./temp --noconfirm --onefile --windowed --specpath ./ --distpath ./ --icon "data\icon.ico" --add-data "data;." --name "SourceViewer" --hidden-import "comtypes.stream" "data\main.py"
   ```

## Download

You can download the already compiled versions from the [releases section](https://github.com/CesarGarza55/SourceViewer/releases/latest/), ready to use and without additional requirements.

Example of use:

![image](https://github.com/user-attachments/assets/99230d0d-a61a-4348-82c5-524bf3b978de)

## How to Use

1. **Start the Application**: Upon launching SourceViewer, you will be presented with options to select your video and audio sources.
2. **Select Video/Audio Sources**: Use the dropdown menus to choose your preferred video and audio input devices.
3. **Start Viewing**: Click the `Start` button to begin streaming video and audio. The video will appear in a new window.
4. **Fullscreen Mode**: Toggle fullscreen mode by pressing the `Fullscreen` button or by pressing `F11` while in the video window.
5. **Close Application**: To stop the video and audio streams, press the `Close` button.

## Update Notification

SourceViewer automatically checks for updates in the GitHub repository. If a new version is available, you will be prompted to download it when you launch the application.

## Contributing

If you wish to contribute to SourceViewer, please fork the repository, create a new branch for your feature or bugfix, and submit a pull request.

## License

SourceViewer is released under the [GPLv2](LICENSE).
