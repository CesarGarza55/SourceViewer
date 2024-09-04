# SourceViewer

**SourceViewer** is a Python application built using `customtkinter` that allows you to visualize video and audio sources connected to your computer. The application provides an easy-to-use interface to select, view, and listen to your media sources.

It is possible that some device is not listed in the application, if so please report it and I will try to add it to the listed devices, this is because in Windows there are dozens of devices and the pyaudio library detects all of them, although not all of them are usable devices.

This project was born from the small number of applications that allow you to view inputs from video capture devices or cameras without the need for applications like OBS that usually consume too many resources, for people who do not need to record their screen this app will allow you to only view it.

## Features

- **Video Source Selection**: Detect and select from available video input devices.
- **Audio Source Selection**: Detect and select from available audio input devices.
- **Audio Output Selector**: Detects and select from available audio output devices.
- **Resolution selector**: Select from a variety of resolution options.
- **FPS selector**: Select from a variety of FPS options.
- **Fullscreen Mode**: View video sources in fullscreen mode.
- **Download Latest Version**: Automatic detection of updates with the option to download the latest release.

## Requirements

- Python 3.12.x
- [pyinstaller](https://pypi.org/project/pyinstaller/)
- [OpenCV](https://pypi.org/project/opencv-python/)
- [Pillow](https://pypi.org/project/Pillow/)
- [pyaudio](https://pypi.org/project/PyAudio/)
- [requests](https://pypi.org/project/requests/)
- [customtkinter](https://pypi.org/project/customtkinter/)
- [pygrabber](https://pypi.org/project/pygrabber/)
- [ffmpegcv](https://pypi.org/project/ffmpegcv/)

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

![image](https://github.com/user-attachments/assets/6ceadbdb-34a9-4ccb-8c76-3b57dac83288)


## How to Use

1. **Start the Application**: Upon launching SourceViewer, you will be presented with options to select your video and audio sources.
2. **Select Video/Audio Sources/Audio Output**: Use the dropdown menus to choose your preferred video and audio input devices and the output.
3. **Select the resolution and FPS**: Use the dropdown menus to choose your preferred resolution and FPS options.
4. **Start Viewing**: Click the `Start` button to begin streaming video and audio. The video will appear in a new window.
5. **Fullscreen Mode**: Toggle fullscreen mode by pressing the `Fullscreen` button or by pressing `F` while in the video window.
6. **Close**: To stop the video and audio streams, press `ESC` or close the video window.

## Update Notification

SourceViewer automatically checks for updates in the GitHub repository. If a new version is available, you will be prompted to download it when you launch the application.

## Bugs

SourceViewer is a personal project and is not intended to compete with professional projects like OBS or VLC. My proposal is a simple and brief solution for my own use, which I decided to share. I spent several hours trying to fix the bug that is currently present, but I couldn't solve it. I know it's probably something very simple, and if I can, I will fix it soon.

![image](https://github.com/user-attachments/assets/cfbf783b-e286-445e-afb9-0535e21d4679)


## Contributing

If you wish to contribute to SourceViewer, please fork the repository, create a new branch for your feature or bugfix, and submit a pull request.

## License

SourceViewer is released under the [GPLv2](LICENSE).
