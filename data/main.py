import json, cv2, os, threading, pyaudio, sys, subprocess, unicodedata, webbrowser, requests, time
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pygrabber.dshow_graph import FilterGraph
import pygame
import numpy as np
from pygame import FULLSCREEN, RESIZABLE, HWSURFACE, DOUBLEBUF
import variables

list_video = []
selected_device = None
# Application name and data path
version = "1.2.0"
appname = "SourceViewer"
appdata = os.environ["APPDATA"]
directory = os.path.join(appdata, appname)
user_data_path = os.path.join(directory, "settings.json")

icon_path = variables.icon_path
video_icon_path = variables.video_icon_path

saved_video_source = 0
saved_audio_source = 0
saved_audio_output = 0
saved_fullscreen = False
saved_resolutions = "1280x720"
saved_fps_options = "30"
saved_fps_check = False

# Function to write a log file
def write_log(text = "", log_type = "latest"):
    text = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n"
    os.makedirs(f'{directory}/logs', exist_ok=True)
    with open(f'{directory}/logs/{log_type}.log', 'a') as f:
        f.write(text)

# Function to handle exceptions and show a messagebox with the error instead of crashing the application directly
def handle_exception(exc_type, exc_value, exc_traceback):
    # Log the exception
    write_log(f"Exception: {exc_type}, {exc_value}", "exception")
    # Show the exception in a messagebox
    # messagebox.showerror("Error", lang(current_language,"error_occurred") + f"\n{exc_type}: {exc_value}")

# Set the exception hook to the handle_exception function
sys.excepthook = handle_exception

# Check if FFmpeg is installed
def check_ffmpeg_installed():
    try:
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "ffmpeg version" in result.stdout:
            return True
        else:
            raise FileNotFoundError("FFmpeg not found")
    except FileNotFoundError:
        ask = messagebox.askyesno("FFmpeg not found", "FFmpeg is required to run this application. Do you want to download it?")
        if ask:
            webbrowser.open_new("https://ffmpeg.org/download.html")
            ask2 = messagebox.askyesno("FFmpeg tutorial", "Do you also want to open a tutorial on how to install FFmpeg on Windows?")
            if ask2:
                webbrowser.open_new("https://github.com/CesarGarza55/SourceViewer/blob/main/FFMPEG_PATH.md")
            sys.exit()
        else:
            messagebox.showerror("FFmpeg not found", "FFmpeg is required to run this application. Please install it.")
            sys.exit()

# Check if FFmpeg is installed
check_ffmpeg_installed()

import ffmpegcv as fc

def center_window(window):
    window.update()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def download_file(url, dest, progress_window, progress_var, progress_bar, progress_label):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0)) or 1
    block_size = 1024
    downloaded_size = 0
    
    with open(dest, 'wb') as file:
        for data in response.iter_content(block_size):
            if progress_window.winfo_exists():
                file.write(data)
                downloaded_size += len(data)
                progress = (downloaded_size / total_size) * 100
                progress_var.set(progress)
                progress_bar['value'] = progress
                progress_label.config(text=f"{int(progress)}%")
                progress_window.update()
            else:
                return False
    return True

def check_update():
    try:
        response = requests.get("https://github.com/CesarGarza55/SourceViewer/releases/latest")
        latest_version = response.url.split('/')[-1]

        if latest_version > version:
            root = tk.Tk()
            root.withdraw()
            if messagebox.askyesno("Update", f"Version {latest_version} is available. Download?"):
                download_location = filedialog.askdirectory()
                if download_location:
                    progress_window = tk.Toplevel(root)
                    center_window(progress_window)
                    progress_window.title("Downloading Update")
                    progress_window.geometry("300x150")
                    progress_window.resizable(False, False)
                    progress_window.attributes('-topmost', True)
                    progress_window.iconbitmap(icon_path)
                    
                    tk.Label(progress_window, text="Downloading update...").pack(pady=10)
                    progress_var = tk.DoubleVar()
                    progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
                    progress_bar.pack(pady=10, padx=20, fill=tk.X)
                    progress_label = tk.Label(progress_window, text="0%")
                    progress_label.pack()
                    
                    
                    url = f"https://github.com/CesarGarza55/SourceViewer/releases/latest/download/SourceViewer.exe"
                    dest = f'{download_location}/SourceViewer-{latest_version}.exe'
                    
                    if download_file(url, dest, progress_window, progress_var, progress_bar, progress_label):
                        progress_window.destroy()
                        messagebox.showinfo("Success", "Update downloaded successfully!")
                        os.system(f'start {dest}')
                        sys.exit()
            root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Update check failed: {str(e)}")

# Check for updates
check_update()

if os.path.exists(f'{user_data_path}'):
    with open(f'{directory}/settings.json', 'r') as f:
        user_data = json.load(f)
        saved_video_source = int(user_data.get('video_source', 0))
        saved_audio_source = int(user_data.get('audio_source', 0))
        saved_audio_output = int(user_data.get('audio_output', 0))
        saved_fullscreen = user_data.get('fullscreen', False)
        saved_resolutions = user_data.get('resolutions', "1280x720")
        saved_fps_options = user_data.get('fps_options', "30")
        saved_fps_check = user_data.get('show_fps', False)
else:
    os.makedirs(f'{directory}', exist_ok=True)
    with open(user_data_path, 'w') as f:
        data = {
            "video_source": "0",
            "audio_source": "0",
            "audio_output": "0"
        }
        json.dump(data, f)
        saved_video_source = 0
        saved_audio_source = 0
        saved_audio_output = 0

class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{appname} - Settings")
        window_width = 400
        window_height = 650
        x_position = 50
        y_position = 50
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.resizable(False, False)
        self.root.iconbitmap(icon_path)

        # Variables
        global saved_video_source, saved_audio_source, saved_audio_output, saved_fullscreen, saved_resolutions, saved_fps_options, saved_fps_check
        self.video_source = saved_video_source
        self.audio_source = saved_audio_source
        self.audio_output = saved_audio_output
        self.is_fullscreen = saved_fullscreen
        self.show_fps = saved_fps_check
        self.cap = None
        self.audio_stream = None
        self.audio_output_stream = None
        self.video_window = None
        self.video_thread = None
        self.audio_thread = None
        self.stop_threads = threading.Event()
        self.info_window = None
        self.help_window = None

        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)  # Reduced padding

        # Title and controls in same row
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.pack(fill=ctk.X, pady=(0, 15))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text=appname,
            font=("Arial Bold", 24)
        )
        self.title_label.pack(side=ctk.LEFT, padx=10)

        # Help and Info buttons with better contrast
        self.help_btn = ctk.CTkButton(
            self.header_frame,
            text="?",
            width=30,
            height=30,
            command=self.show_help,
            corner_radius=15,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d"
        )
        self.help_btn.pack(side=ctk.RIGHT, padx=(0,5))

        self.info_btn = ctk.CTkButton(
            self.header_frame,
            text="i",
            width=30,
            height=30,
            command=self.show_info,
            corner_radius=15,
            fg_color="#3d3d3d",
            hover_color="#4d4d4d"
        )
        self.info_btn.pack(side=ctk.RIGHT, padx=5)

        # Sources frame
        self.sources_frame = ctk.CTkFrame(self.main_frame)
        self.sources_frame.pack(fill=ctk.X, pady=(0, 15))

        # Create combo boxes
        self.video_sources = ctk.CTkComboBox(self.sources_frame)
        self.audio_sources = ctk.CTkComboBox(self.sources_frame)
        self.audio_outputs = ctk.CTkComboBox(self.sources_frame)

        labels = ["Video Source:", "Audio Input:", "Audio Output:"]
        combos = [self.video_sources, self.audio_sources, self.audio_outputs]

        for label_text, combo in zip(labels, combos):
            ctk.CTkLabel(self.sources_frame, text=label_text, anchor="w").pack(pady=(8,0), padx=10)
            combo.configure(state="readonly", command=lambda x: self.save_settings())
            combo.pack(pady=(0,8), padx=10, fill=ctk.X)

        # Settings frame
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_frame.pack(fill=ctk.X, pady=(0, 15))

        # Create combo boxes
        self.resolutions = ctk.CTkComboBox(self.settings_frame)
        self.fps_options = ctk.CTkComboBox(self.settings_frame)

        settings_labels = ["Resolution:", "Frame Rate:"]
        settings_combos = [self.resolutions, self.fps_options]

        for label_text, combo in zip(settings_labels, settings_combos):
            ctk.CTkLabel(self.settings_frame, text=label_text, anchor="w").pack(pady=(8,0), padx=10)
            combo.configure(state="readonly", command=lambda x: self.save_settings())
            combo.pack(pady=(0,8), padx=10, fill=ctk.X)

        # Controls frame
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.pack(fill=ctk.X)

        # Create Show FPS checkbox
        self.show_fps_var = tk.IntVar()
        self.show_fps_var.set(0)
        self.show_fps_check = ctk.CTkCheckBox(
            self.controls_frame,
            text="Show FPS",
            variable=self.show_fps_var,
            command=lambda: self.save_settings()
        )
        self.show_fps_check.pack(pady=(8,0), padx=10, fill=ctk.X)

        # Create buttons
        buttons = [
            ("Start", self.open_video_window, "#2ea043", "#3fae54", 4),
            ("Test Resolutions", self.show_test_results, None, None, 4),
            ("Close", self.close_window, "#d93848", "#e94858", 4)
        ]

        for text, cmd, fg, hover, pady in buttons:
            btn = ctk.CTkButton(
                self.controls_frame,
                text=text,
                command=cmd,
                fg_color=fg if fg else None,
                hover_color=hover if hover else None,
                state=ctk.DISABLED if text == "Fullscreen" else ctk.NORMAL
            )
            btn.pack(pady=pady, padx=10, fill=ctk.X)
            if text == "Start": self.start_btn = btn
            elif text == "Close": self.close_btn = btn
            elif text == "Test Resolutions": self.test_btn = btn

        # Initialize sources
        self.detect_video_sources()
        self.detect_audio_sources()
        self.detect_audio_outputs()
        self.detect_resolutions()
        self.detect_fps_options()
        self.detect_fps_check()

        root.bind("<F11>", self.toggle_fullscreen_event)

    def detect_resolutions(self):
        global saved_resolutions
        # Add common resolutions
        resolutions = ["640x480", "800x600", "1024x768", "1280x720", "1366x768", "1920x1080", "3840x2160"]
        self.resolutions.configure(values=resolutions)
        self.resolutions.set(saved_resolutions)  # Set default resolution

    def detect_fps_options(self):
        global saved_fps_options
        # Add common FPS options
        fps_options = ["15", "24", "30", "60", "75", "120", "240"]
        self.fps_options.configure(values=fps_options)
        self.fps_options.set(saved_fps_options)  # Set default FPS (30)

    def detect_fps_check(self):
        global saved_fps_check
        self.show_fps_var.set(saved_fps_check)

    def save_settings(self):
        global saved_video_source, saved_audio_source, saved_audio_output
        video_source = self.video_sources.get().split()
        audio_source = self.audio_sources.get().split()
        audio_output = self.audio_outputs.get().split()
        if len(video_source) > 1:
            saved_video_source = video_source[1].replace(':', '')
        if len(audio_source) > 1:
            saved_audio_source = audio_source[1].replace(':', '')
        if len(audio_output) > 1:
            saved_audio_output = audio_output[1].replace(':', '')
        os.makedirs(f'{directory}', exist_ok=True)
        # Save the data to a file
        data = {
            'video_source': saved_video_source,
            'audio_source': saved_audio_source,
            'audio_output': saved_audio_output,
            'fullscreen': self.is_fullscreen,
            'resolutions': self.resolutions.get(),
            'fps_options': self.fps_options.get(),
            'show_fps': self.show_fps_var.get()
        }
        # Save data to a file
        with open(f'{user_data_path}', 'w') as f:
            json.dump(data, f)

    def detect_video_sources(self):
        global list_video
        graph = FilterGraph()
        devices = graph.get_input_devices()
        list_video = devices
        sources = [f"Video {i}: {device}" for i, device in enumerate(devices)]

        self.video_sources.configure(values=sources)
        self.video_sources.set(sources[0])
        if sources:
            global saved_video_source
            try:
                if saved_video_source < len(sources):
                    self.video_sources.set(sources[saved_video_source])  # Select the saved video source
                else:
                    self.video_sources.set(sources[0])
                    saved_video_source = 0
                self.video_sources.bind("<<ComboboxSelected>>", self.change_video_source)
            except:
                self.video_sources.set(sources[0])
                self.video_sources.bind("<<ComboboxSelected>>", self.change_video_source)
                self.save_settings()
        else:
            messagebox.showerror("Error", "No available video sources found.")
    
    def clean_device_name(self, name):
        name = unicodedata.normalize('NFD', name)
        name = name.replace("Ã¡", "á")
        name = name.replace("Ã©", "é")
        name = name.replace("Ã­", "í")
        name = name.replace("Ã³", "ó")
        name = name.replace("Ãº", "ú")
        name = name.replace("Ã±", "ñ")
        return name
    
    def is_valid_device_name(self, name):
        return not any(keyword in name for keyword in ["Output", "Virtual", "Unknown", "@System32"])

    def detect_audio_sources(self):
        p = pyaudio.PyAudio()
        sources = []
        seen_device_names = set()
        id = 0
        self.audio_devices = {}
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0 and device_info.get('hostApi') == 0:
                name = self.clean_device_name(device_info['name'])
                if name not in seen_device_names:
                    seen_device_names.add(name)
                    source_name = f"Audio {id}: {name}"
                    sources.append(source_name)
                    self.audio_devices[source_name] = i
                    id += 1

        self.audio_sources.configure(values=sources)
        if sources:
            global saved_audio_source
            try:
                if saved_audio_source < len(sources):
                    self.audio_sources.set(sources[saved_audio_source])  # Select the saved video source
                else:
                    self.audio_sources.set(sources[0])
                    saved_audio_source = 0
                self.audio_sources.bind("<<ComboboxSelected>>", self.change_audio_source)
            except:
                self.audio_sources.set(sources[0])
                self.audio_sources.bind("<<ComboboxSelected>>", self.change_audio_source)
                self.save_settings()
        else:
            messagebox.showerror("Error", "No available audio sources found.")

    def detect_audio_outputs(self):
        p = pyaudio.PyAudio()
        outputs = []
        seen_device_names = set()
        id = 0
        self.audio_output_devices = {}
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info.get('maxOutputChannels') > 0 and device_info.get('hostApi') == 0:
                name = self.clean_device_name(device_info['name'])
                if name not in seen_device_names and not self.is_virtual_device(name):
                    seen_device_names.add(name)
                    output_name = f"Output {id}: {name}"
                    outputs.append(output_name)
                    self.audio_output_devices[output_name] = i
                    id += 1

        self.audio_outputs.configure(values=outputs)
        if outputs:
            global saved_audio_output
            try:
                if saved_audio_output < len(outputs):
                    self.audio_outputs.set(outputs[saved_audio_output])  # Select the saved audio output
                else:
                    self.audio_outputs.set(outputs[0])
                    saved_audio_output = 0
                self.audio_outputs.bind("<<ComboboxSelected>>", self.change_audio_output)
            except:
                self.audio_outputs.set(outputs[0])
                self.audio_outputs.bind("<<ComboboxSelected>>", self.change_audio_output)
                self.save_settings()
        else:
            messagebox.showerror("Error", "No available audio outputs found.")

    def is_virtual_device(self, name):
        virtual_keywords = ["Virtual", "HDMI", "USB Capture"]
        for keyword in virtual_keywords:
            if keyword in name:
                return True
            
        return False
    
    def change_audio_source(self, event):
        selected_source = self.audio_sources.get()
        self.audio_source = self.audio_devices[selected_source]
        self.set_audio_source(self.audio_source)

    def change_audio_output(self, event):
        selected_output = self.audio_outputs.get()
        self.audio_output = self.audio_output_devices[selected_output]
        self.set_audio_output(self.audio_output)

    def set_audio_source(self, source):
        if self.audio_stream is not None:
            if self.audio_stream.is_active():
                self.audio_stream.stop_stream()
            self.audio_stream.close()
        p = pyaudio.PyAudio()
        device_info = p.get_device_info_by_index(source)
        max_sample_rate = device_info['defaultSampleRate']
        self.audio_stream = p.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=int(max_sample_rate),
                                input=True,
                                input_device_index=source,
                                frames_per_buffer=2048)

    def set_audio_output(self, output):
        if self.audio_output_stream is not None:
            if self.audio_output_stream.is_active():
                self.audio_output_stream.stop_stream()
            self.audio_output_stream.close()
        p = pyaudio.PyAudio()
        device_info = p.get_device_info_by_index(output)
        max_sample_rate = device_info['defaultSampleRate']
        self.audio_output_stream = p.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=int(max_sample_rate),
                                        output=True,
                                        output_device_index=output)

    def set_video_source(self, source):
        if self.cap:
            self.cap.release()
        graph = FilterGraph()
        devices = graph.get_input_devices()
        name = devices[source]
        
        # Search for the device index
        device_index = None
        for index, device_name in enumerate(devices):
            if device_name == name:
                device_index = index
                break
        
        if device_index is not None:
            global selected_device, list_video
            selected_device = name
        else:
            raise ValueError(f"Device {name} not found")

    def change_video_source(self, event):
        selected_source = self.video_sources.get()
        self.video_source = int(selected_source.split()[1].replace(':', ''))
        self.set_video_source(self.video_source)

    def show_test_results(self):
        # Ask the user to confirm the test
        if not messagebox.askyesno("Test Resolutions and FPS", "This will test all resolutions and FPS options for the selected video source to find stable combinations. This process may take a few minutes. Do you want to continue?"):
            return
        # Create a progress window
        progress_window = ctk.CTkToplevel(self.root)
        progress_window.title("Testing Resolutions and FPS")
        progress_window.geometry("300x150")
        progress_window.resizable(False, False)
        progress_window.lift()  # Ensure the window is on top
        progress_window.attributes("-topmost", True)  # Keep the window on top
        self.root.after(200, lambda: progress_window.iconbitmap(icon_path))
        
        progress_label = ctk.CTkLabel(progress_window, text="Testing, please wait...", font=("Arial", 12))
        progress_label.pack(pady=5)
        
        info_label = ctk.CTkLabel(progress_window, text="This will test all resolutions and FPS options, this process may take a few minutes.", font=("Arial", 12))
        info_label.pack(pady=5)
        info_label.configure(wraplength=280)
        
        progress_bar = ctk.CTkProgressBar(progress_window, mode='indeterminate')
        progress_bar.pack(padx=20, pady=10, fill=ctk.X)
        progress_bar.start()

        # Flag to control the test execution
        self.stop_test = False

        def on_progress_window_close():
            self.stop_test = True
            progress_bar.stop()  # Stop the progress bar
            progress_window.destroy()

        progress_window.protocol("WM_DELETE_WINDOW", on_progress_window_close)

        # Run the test in a separate thread to keep the UI responsive
        def run_tests():
            stable_combinations = self.test_resolutions_and_fps()
            if self.stop_test:
                return
            
            results_dict = {}
            for res, fps in stable_combinations:
                if res not in results_dict:
                    results_dict[res] = fps
                else:
                    results_dict[res] = max(results_dict[res], fps)
            
            results = "\n".join([f"{res} up to {fps} FPS" for res, fps in results_dict.items()])
            if not results:
                results = "No stable combinations found."
            
            # Close the progress window
            progress_bar.stop()  # Stop the progress bar
            progress_window.destroy()
            
            # Create a new window to display the results
            results_window = ctk.CTkToplevel(self.root)
            results_window.title("Test Results")
            results_window.geometry("400x300")
            results_window.resizable(False, False)
            results_window.lift()
            results_window.attributes("-topmost", True)
            results_window.after(200, lambda: results_window.iconbitmap(icon_path))
            
            results_label = ctk.CTkLabel(results_window, text="Stable Resolutions and FPS:", font=("Arial", 16))
            results_label.pack(pady=10)

            info_label = ctk.CTkLabel(results_window, text="The following resolutions and FPS options are stable for the selected video source:", font=("Arial", 14))
            info_label.pack(pady=5)
            info_label.configure(wraplength=380)
            
            results_text = ctk.CTkTextbox(results_window, wrap=ctk.WORD, font=("Arial", 16))
            results_text.insert(ctk.END, results)
            results_text.configure(state=ctk.DISABLED)
            results_text.pack(padx=10, pady=10, fill=ctk.BOTH, expand=True)

        # Start the test in a new thread
        threading.Thread(target=run_tests).start()

    def test_resolutions_and_fps(self):
        #resolutions = ["640x480", "800x600", "1024x768", "1280x720", "1366x768", "1920x1080", "3840x2160"]
        #fps_options = ["15", "24", "30", "60", "75", "120", "240"]
        # For testing purposes, use a smaller set of resolutions and FPS options
        resolutions = ["1280x720", "1920x1080"]
        fps_options = ["30", "60"]
        stable_combinations = []

        for resolution in resolutions:
            if self.stop_test:
                break
            width, height = map(int, resolution.split('x'))
            for fps in fps_options:
                if self.stop_test:
                    break
                fps = int(fps)
                print(f"Testing {resolution} at {fps} FPS...")
                if self.test_combination(width, height, fps):
                    stable_combinations.append((resolution, fps))
                    print(f"Stable: {resolution} at {fps} FPS")
                else:
                    print(f"Unstable: {resolution} at {fps} FPS")

        return stable_combinations

    def test_combination(self, width, height, fps):
        pygame.init()
        screen = pygame.display.set_mode((width, height), RESIZABLE | HWSURFACE | DOUBLEBUF | pygame.HIDDEN)
        pygame.display.set_caption(f"Testing {width}x{height} @ {fps} FPS")
        
        clock = pygame.time.Clock()
        
        # Setting up video capture
        self.set_video_source(self.video_source)
        
        self.cap = fc.VideoCaptureCAM(selected_device, camsize_wh=(width, height), camfps=fps)
        
        if not self.cap.isOpened():
            print(f"Failed to open video capture device for {width}x{height} @ {fps} FPS")
            pygame.quit()
            return False

        ret, frame = self.cap.read()
        if not ret:
            print(f"Failed to read frame from video capture device for {width}x{height} @ {fps} FPS")
            self.cap.release()
            pygame.quit()
            return False

        frame_count = 0
        stable = True
        fps_threshold = 0.8 * fps  # Adjust the threshold to 80% of the desired FPS

        while frame_count < 60:  # Test for 60 frames
            if self.stop_test:
                stable = False
                break
            ret, frame = self.cap.read()
            if not ret:
                stable = False
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surf = pygame.surfarray.make_surface(frame.swapaxes(0,1))
            screen.fill((0,0,0))
            screen.blit(surf, (0, 0))
            pygame.display.flip()

            clock.tick(fps)
            actual_fps = clock.get_fps()
            print(f"Frame: {frame_count}, Actual FPS: {actual_fps}, Threshold: {fps_threshold}")  # Debugging line
            if frame_count > 12 and actual_fps < fps_threshold:  # Add delay before checking FPS stability
                stable = False
                break

            frame_count += 1

        self.cap.release()
        pygame.quit()
        return stable

    def open_video_window(self):
        # Make sure the video and audio source are updated before opening the video window
        self.change_video_source(None)
        self.change_audio_source(None)
        self.change_audio_output(None)

        # Setting up video and audio capture
        self.set_video_source(self.video_source)
        self.set_audio_source(self.audio_source)
        self.set_audio_output(self.audio_output)
        
        # Start capturing video and audio in separate threads
        self.stop_threads.clear()
        self.video_thread = threading.Thread(target=self.update_video, daemon=True)
        self.audio_thread = threading.Thread(target=self.update_audio, daemon=True)
        self.video_thread.start()
        self.audio_thread.start()

    def create_hint_overlay(self):
        hint_texts = ["ESC: Close Video", "F: Toggle Fullscreen", "S: Show FPS"]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        padding = 10
        
        # Get text sizes to calculate overlay dimensions
        text_sizes = [cv2.getTextSize(text, font, font_scale, thickness)[0] for text in hint_texts]
        overlay_width = max(size[0] for size in text_sizes) + padding * 2
        line_height = 40
        overlay_height = len(hint_texts) * line_height
        
        # Create transparent overlay (4 channels - RGBA)
        hint_overlay = np.zeros((overlay_height, overlay_width, 4), dtype=np.uint8)
        
        # Draw each line with background
        for i, text in enumerate(hint_texts):
            text_size = text_sizes[i]
            x_pos = (overlay_width - text_size[0]) // 2
            y_pos = (i * line_height) + 30
            
            # Calculate background rectangle coordinates
            y1 = y_pos - text_size[1] - padding//2
            y2 = y_pos + padding//2
            x1 = x_pos - padding
            x2 = x_pos + text_size[0] + padding
            
            # Draw black background for this line
            hint_overlay[y1:y2, x1:x2, :3] = 0  # Black color
            hint_overlay[y1:y2, x1:x2, 3] = 255  # Full opacity
            
            # Draw text in white
            cv2.putText(hint_overlay, text, (x_pos, y_pos),
                    font, font_scale, (255, 255, 255, 255), thickness)
            # Make text fully opaque
            text_mask = hint_overlay[:, :, 0] > 0  # Where text is white
            hint_overlay[text_mask, 3] = 255
        
        return hint_overlay

    def update_video(self):
        # Enable hardware acceleration
        os.environ['SDL_HINT_RENDER_DRIVER'] = 'direct3d'
        fullscreen = self.is_fullscreen
        width = int(self.resolutions.get().split('x')[0])
        height = int(self.resolutions.get().split('x')[1])
        fps = int(self.fps_options.get())
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Force fullscreen CV2 if resolution matches monitor
        if width == screen_width and height == screen_height:
            fullscreen = True
            self.is_fullscreen = True
            pygame_active = False
        else:
            pygame_active = not fullscreen

        self.start_btn.configure(state=tk.DISABLED)
        
        # Initialize camera
        self.cap = fc.VideoCaptureCAM(selected_device, camsize_wh=(width, height), camfps=fps)
        
        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to open the video capture device...")
            self.close_video_window()
            self.start_btn.configure(state=tk.NORMAL)
            return
        
        clock = pygame.time.Clock()
        running = True
        original_size = (width, height)
        pygame_active = not fullscreen
        screen = None
        font = None
        
        # Initialize based on mode
        if fullscreen:
            # Setup fullscreen CV2 window
            cv2.namedWindow(appname, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(appname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            # Initialize pygame for windowed mode
            pygame.init()
            screen = pygame.display.set_mode((width, height), RESIZABLE | HWSURFACE | DOUBLEBUF)
            pygame.display.set_caption(appname)
            pygame.display.set_icon(pygame.image.load(video_icon_path))
            font = pygame.font.Font(None, 28)
        
        # Pre-create overlay for FPS display
        fps_overlay = np.zeros((50, 150, 3), dtype=np.uint8)

        # Add after mode initialization:
        hint_overlay = self.create_hint_overlay()
        hint_start_time = time.time()
        hint_duration = 3.0  # seconds

        while running and not self.stop_threads.is_set():
            if pygame_active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if fullscreen:
                                cv2.destroyWindow(appname)
                                pygame_active = True
                                pygame.init()
                                screen = pygame.display.set_mode(original_size, RESIZABLE | HWSURFACE | DOUBLEBUF)
                                pygame.display.set_caption(appname)
                                pygame.display.set_icon(pygame.image.load(video_icon_path))
                                font = pygame.font.Font(None, 28)  # Add font initialization
                                fullscreen = False
                            else:
                                running = False
                        elif event.key == pygame.K_f or event.key == pygame.K_F11:
                            hint_start_time = time.time()
                            fullscreen = not fullscreen
                            self.is_fullscreen = fullscreen 
                            self.save_settings()
                            if fullscreen:
                                pygame.display.quit()
                                pygame_active = False
                                font = None
                            else:
                                cv2.destroyWindow(appname)
                                pygame_active = True
                                pygame.init()
                                screen = pygame.display.set_mode(original_size, RESIZABLE | HWSURFACE | DOUBLEBUF)
                                pygame.display.set_caption(appname)
                                pygame.display.set_icon(pygame.image.load(video_icon_path))
                                font = pygame.font.Font(None, 28)  # Initialize font when switching to windowed
                        elif event.key == pygame.K_s:
                            self.show_fps_var.set(not self.show_fps_var.get())
                            self.save_settings()
                    elif event.type == pygame.VIDEORESIZE and not fullscreen:
                        width, height = event.size
                        screen = pygame.display.set_mode((width, height), RESIZABLE | HWSURFACE | DOUBLEBUF)
                        original_size = (width, height)

            ret, frame = self.cap.read()
            current_time = time.time()
            show_hint = current_time - hint_start_time < hint_duration
            if ret:
                if fullscreen:
                    # Make a copy of the frame for modification
                    display_frame = frame.copy()
                    if show_hint:
                        h, w = hint_overlay.shape[:2]
                        y_pos = display_frame.shape[0] - h - 20
                        x_pos = (display_frame.shape[1] - w) // 2
                        
                        # Extract region where we'll overlay the hint
                        roi = display_frame[y_pos:y_pos+h, x_pos:x_pos+w]
                        
                        # Calculate alpha factor based on time
                        alpha_factor = max(0, min(1, hint_duration - (current_time - hint_start_time)))
                        
                        # Blend only where the hint overlay is not transparent
                        alpha_mask = (hint_overlay[:, :, 3] / 255.0) * alpha_factor
                        alpha_mask = np.stack([alpha_mask] * 3, axis=2)
                        
                        # Blend the overlay with the frame
                        roi_blend = (1.0 - alpha_mask) * roi + alpha_mask * hint_overlay[:, :, :3]
                        display_frame[y_pos:y_pos+h, x_pos:x_pos+w] = roi_blend.astype(np.uint8)
                    if self.show_fps_var.get():
                        fps_overlay.fill(0)
                        fps_text = f"FPS: {int(clock.get_fps())}"
                        cv2.putText(fps_overlay, fps_text, (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        # Blend FPS overlay
                        display_frame[0:50, 0:150] = cv2.addWeighted(
                            display_frame[0:50, 0:150], 1.0,
                            fps_overlay, 1.0, 0
                        )
                    
                    cv2.namedWindow(appname, cv2.WND_PROP_FULLSCREEN)
                    cv2.setWindowProperty(appname, cv2.WND_PROP_FULLSCREEN, 
                                        cv2.WINDOW_FULLSCREEN)
                    cv2.imshow(appname, display_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('f') or key == ord('F'):
                        if width != screen_width or height != screen_height:
                            hint_start_time = time.time()
                            fullscreen = False
                            self.is_fullscreen = fullscreen
                            self.save_settings()
                            cv2.destroyWindow(appname)
                            pygame_active = True
                            pygame.init()
                            screen = pygame.display.set_mode(original_size, RESIZABLE | HWSURFACE | DOUBLEBUF)
                            pygame.display.set_caption(appname)
                            pygame.display.set_icon(pygame.image.load(video_icon_path))
                            font = pygame.font.Font(None, 28)
                    elif key == ord('s') or key == ord('S'):
                        self.show_fps_var.set(not self.show_fps_var.get())
                        self.save_settings()
                    elif key == 27:
                        running = False
                elif pygame_active:
                    # Pygame windowed mode
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0,1))
                    
                    screen_rect = screen.get_rect()
                    frame_aspect = frame.shape[1] / frame.shape[0]
                    screen_aspect = screen_rect.width / screen_rect.height
                    
                    if screen_aspect > frame_aspect:
                        display_height = screen_rect.height
                        display_width = int(display_height * frame_aspect)
                    else:
                        display_width = screen_rect.width
                        display_height = int(display_width / frame_aspect)
                    
                    scaled_surface = pygame.transform.smoothscale(surf, (display_width, display_height))
                    rect = scaled_surface.get_rect(center=screen_rect.center)
                    
                    screen.fill((0,0,0))
                    screen.blit(scaled_surface, rect)
                    
                    if self.show_fps_var.get() and font is not None:  # Check if font exists
                        fps_text = f"FPS: {int(clock.get_fps())}"
                        text = font.render(fps_text, True, (255,255,255))
                        screen.blit(text, (10, 10))

                    # Show hint overlay
                    if show_hint and font:
                        hint_texts = ["S: Show FPS", "F: Toggle Fullscreen", "ESC: Close Video"]
                        alpha = int(255 * max(0, min(1, hint_duration - (current_time - hint_start_time))))
                        
                        for i, text in enumerate(hint_texts):
                            text_surf = font.render(text, True, (255,255,255), (0,0,0, alpha))
                            text_rect = text_surf.get_rect(center=(screen_rect.centerx, screen_rect.bottom - 30 - i * 30))
                            screen.blit(text_surf, text_rect)
                            
                    pygame.display.flip()
                
                current_size = original_size if not fullscreen else (frame.shape[1], frame.shape[0])
                if pygame_active:
                    pygame.display.set_caption(f"{appname} - {current_size[0]}x{current_size[1]} @ {fps} FPS")
                
                clock.tick(fps)

        # Cleanup
        if self.cap is not None:
            self.cap.release()
        if pygame_active:
            pygame.quit()
        cv2.destroyAllWindows()
        self.start_btn.configure(state=tk.NORMAL)
        self.close_video_window()

    def update_image(self, ctk_img):
        if self.video_window and self.video_window.winfo_exists():
            self.video_label.configure(image=ctk_img)

    def update_audio(self):
        while not self.stop_threads.is_set():
            if self.audio_stream and self.audio_stream.is_active():
                try:
                    data = self.audio_stream.read(2048, exception_on_overflow=False) # Read more data with a larger buffer
                    # Play the captured audio
                    self.audio_output_stream.write(data)
                except IOError:
                    continue

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.save_settings()

    def toggle_fullscreen_event(self, event):
        self.toggle_fullscreen

    def close_audio_stream(self):
        if self.audio_stream is not None:
            if self.audio_stream.is_active():
                self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if self.audio_output_stream is not None:
            if self.audio_output_stream.is_active():
                self.audio_output_stream.stop_stream()
            self.audio_output_stream.close()
            self.audio_output_stream = None

    def close_video_window(self):
        self.stop_threads.set()
        
        # Wait for the threads to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
        
        # Close the audio stream
        self.close_audio_stream()       
        
        # Close the video stream
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Close the video window
        cv2.destroyAllWindows()

    def close_window(self):
        self.stop_threads.set()
        current_thread = threading.current_thread()
        if self.video_thread and self.video_thread is not current_thread:
            self.video_thread.join(timeout=1)
        if self.audio_thread and self.audio_thread is not current_thread:
            self.audio_thread.join(timeout=1)
        self.close_audio_stream()
        if self.cap:
            self.cap.release()
        if self.video_window:
            self.video_window.destroy()
        self.root.destroy()

    def show_info(self):
        if self.info_window is not None and self.info_window.winfo_exists():
            self.info_window.lift()
            return

        self.info_window = ctk.CTkToplevel(self.root)
        self.info_window.title("About")
        root.after(200, lambda: self.info_window.iconbitmap(icon_path))
        
        # Window setup
        window_width = 400
        window_height = 350
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.info_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.info_window.resizable(False, False)

        # App info section
        title_label = ctk.CTkLabel(
            self.info_window, 
            text=appname,
            font=("Arial Bold", 24)
        )
        title_label.pack(pady=(20,5))

        version_label = ctk.CTkLabel(
            self.info_window,
            text=f"Version {version}",
            font=("Arial", 14)
        )
        version_label.pack(pady=(0,15))

        separator = ctk.CTkFrame(self.info_window, height=2)
        separator.pack(fill="x", padx=20, pady=10)

        desc_text = "Source Viewer is an application that allows you to visualize video and audio sources from your computer. It supports multiple video and audio sources, as well as different resolutions and frame rates."
        desc_label = ctk.CTkLabel(
            self.info_window,
            text=desc_text,
            font=("Arial", 12),
            wraplength=350
        )
        desc_label.pack(pady=10, padx=25)

                # Developer section
        dev_frame = ctk.CTkFrame(self.info_window)
        dev_frame.pack(pady=20, fill="x", padx=25)

        creator_label = ctk.CTkLabel(
            dev_frame,
            text="Created by CesarGarza55",
            font=("Arial Bold", 14)
        )
        creator_label.pack(pady=(5,2))

        company_label = ctk.CTkLabel(
            dev_frame,
            text="A project by CodevBox",
            font=("Arial", 13)
        )
        company_label.pack(pady=(0,5))

        def open_website(event):
            webbrowser.open_new("https://codevbox.com")

        website_label = ctk.CTkLabel(
            dev_frame,
            text="https://codevbox.com",
            text_color="#5ca3ff",
            cursor="hand2",
            font=("Arial", 12, "underline")
        )
        website_label.pack(pady=2)
        website_label.bind("<Button-1>", open_website)

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.lift()
            return

        self.help_window = ctk.CTkToplevel(self.root)
        self.help_window.title("Help")
        root.after(200, lambda: self.help_window.iconbitmap(icon_path))
        
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.help_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.help_window.resizable(False, False)

        # Title
        title_label = ctk.CTkLabel(
            self.help_window,
            text="How to Use",
            font=("Arial Bold", 24)
        )
        title_label.pack(pady=20)

        # Quick Start Section
        quick_start = ctk.CTkLabel(
            self.help_window,
            text="Quick Start Guide",
            font=("Arial Bold", 14)
        )
        quick_start.pack(pady=(0,10))

        steps = [
            "1. Select a video source from the dropdown menu",
            "2. Select an audio source from the dropdown menu",
            "3. Use the 'Start' button to open the video window",
            "4. Use 'F' key or 'Fullscreen' button to toggle fullscreen mode",
            "5. Use 'Esc' key to close the video window"
        ]

        for step in steps:
            step_label = ctk.CTkLabel(
                self.help_window,
                text=step,
                font=("Arial", 12),
                justify="left"
            )
            step_label.pack(pady=5, padx=25, anchor="w")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    
    def on_closing():
        # Close the window
        app.close_window()
        # Stop the video
        pygame.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    app = VideoApp(root)
    root.mainloop()