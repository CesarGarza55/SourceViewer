# How to Install FFmpeg and Add it to PATH on Windows

## Step 1: Download FFmpeg

1. Go to the official FFmpeg website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html).
2. Under "Get packages & executable files," click on **Windows** to access FFmpeg builds for Windows.
3. Choose one of the pre-built binaries. You can get a stable release from the recommended source, like [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
4. Download the latest **full build** by selecting the `release full` version (usually available as a .zip file).

## Step 2: Extract FFmpeg

1. Once the download completes, extract the .zip file to a folder on your system.
2. You can place the extracted folder anywhere, but for simplicity, you might want to put it directly in your C: drive (e.g., `C:\ffmpeg`).

## Step 3: Add FFmpeg to the System PATH

1. Press `Windows + R`, type `sysdm.cpl`, and press Enter. This will open the **System Properties** window.
2. In the **System Properties** window, go to the **Advanced** tab and click on **Environment Variables** at the bottom.
3. Under the **System variables** section, scroll down and find the `Path` variable. Select it and click **Edit**.
4. In the **Edit Environment Variable** window, click **New** and add the path to the `bin` folder inside the FFmpeg directory (e.g., `C:\ffmpeg\bin`).
5. Click **OK** to close all windows.

## Step 4: Verify the Installation

1. Open a new Command Prompt by pressing `Windows + R`, typing `cmd`, and pressing Enter.
2. In the Command Prompt, type the following command:
    ```
    ffmpeg -version
    ```
3. If FFmpeg is installed correctly, you should see information about the installed FFmpeg version.
