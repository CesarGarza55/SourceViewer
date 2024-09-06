import json, cv2, os, threading, pyaudio, sys, subprocess, unicodedata, webbrowser, requests
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pygrabber.dshow_graph import FilterGraph

list_video = []
selected_device = None
# Application name and data path
version = "1.1.0"
appname = "SourceViewer"
appdata = os.environ["APPDATA"]
directory = os.path.join(appdata, appname)
user_data_path = os.path.join(directory, "settings.json")

script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "icon_app.ico")

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
try:
    # Obtain the latest version of the application
    update = requests.get("https://api.github.com/repos/CesarGarza55/SourceViewer/releases/latest")
    latest_release = update.json()["tag_name"]

    if latest_release > version:
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Update", f"A new version {latest_release} is available. Would you like to download it?"):
            messagebox.showinfo("Download", "Please select the download location.")
            download_location = filedialog.askdirectory()
            if download_location:
                messagebox.showinfo("Download", "The download is in progress, please wait...")
                # Download the latest version of the application
                r = requests.get(f"https://github.com/CesarGarza55/SourceViewer/releases/latest/download/SourceViewer.exe", allow_redirects=True)
                with open(f'{download_location}/{appname}-{latest_release}.exe', 'wb') as f:
                    f.write(r.content)
                messagebox.showinfo("Download", "The download has been completed successfully.")
                sys.exit()
        root.destroy()
except requests.RequestException as e:
    messagebox.showerror("Network error:", e)
except Exception as e:
    messagebox.showerror("Error:", e)

if os.path.exists(f'{user_data_path}'):
    with open(f'{directory}/settings.json', 'r') as f:
        user_data = json.load(f)
        saved_video_source = int(user_data.get('video_source', 0))
        saved_audio_source = int(user_data.get('audio_source', 0))
        saved_audio_output = int(user_data.get('audio_output', 0))
        saved_fullscreen = user_data.get('fullscreen', False)
        saved_resolutions = user_data.get('resolutions', "1280x720")
        saved_fps_options = user_data.get('fps_options', "30")
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
        window_width = 300
        window_height = 425
        x_position = 50
        y_position = 50
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.resizable(False, False)
        self.root.iconbitmap(icon_path)

        # Variables
        global saved_video_source, saved_audio_source, saved_audio_output, saved_fullscreen
        self.video_source = saved_video_source
        self.audio_source = saved_audio_source
        self.audio_output = saved_audio_output
        self.is_fullscreen = saved_fullscreen
        self.cap = None
        self.audio_stream = None
        self.audio_output_stream = None
        self.video_window = None
        self.video_thread = None
        self.audio_thread = None
        self.stop_threads = threading.Event()
        self.info_window = None
        self.help_window = None

        # Frame for controls in the main window
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill=ctk.BOTH, expand=True)

        # Combobox to select the video source
        self.video_sources = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.video_sources.pack(pady=(40, 10), fill=ctk.BOTH, expand=True)

        # Combobox to select the audio source
        self.audio_sources = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.audio_sources.pack(pady=10, fill=ctk.BOTH, expand=True)

        # Combobox to select the audio output
        self.audio_outputs = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.audio_outputs.pack(pady=10, fill=ctk.BOTH, expand=True)

        # Combobox to select the resolution
        self.resolutions = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.resolutions.pack(pady=10, fill=ctk.BOTH, expand=True)

        # Combobox to select the FPS
        self.fps_options = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.fps_options.pack(pady=10, fill=ctk.BOTH, expand=True)

        # Button to start video capture
        self.start_btn = ctk.CTkButton(self.control_frame, text="Start", command=self.open_video_window)
        self.start_btn.configure(fg_color="green", hover_color="darkgreen")
        self.start_btn.pack(pady=10, fill=ctk.BOTH, expand=True)

        # Full screen button
        self.fullscreen_btn = ctk.CTkButton(self.control_frame, text="Fullscreen", command=self.toggle_fullscreen)
        self.fullscreen_btn.pack(pady=10, fill=ctk.BOTH, expand=True)
        self.fullscreen_btn.configure(state=ctk.DISABLED)

        # Close button
        self.close_btn = ctk.CTkButton(self.control_frame, text="Close", command=self.close_window)
        self.close_btn.pack(pady=10, fill=ctk.BOTH, expand=True)

        # Info button (small and at the top right)
        self.info_btn = ctk.CTkButton(self.root, text="i", width=20, height=20, command=self.show_info)
        self.info_btn.place(relx=1.0, rely=0.0, anchor="ne", x=0, y=10)

        # Help button (small and at the top right)
        self.help_btn = ctk.CTkButton(self.root, text="?", width=20, height=20, command=self.show_help)
        self.help_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-25, y=10)

        # Title label
        self.title_label = ctk.CTkLabel(self.control_frame, text="Visualize your video and audio sources")
        self.title_label.place(relx=0.0, rely=0.0, anchor="nw", x=5, y=5)

        # Detect available video and audio sources
        self.detect_video_sources()
        self.detect_audio_sources()
        self.detect_audio_outputs()
        self.detect_resolutions()
        self.detect_fps_options()

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
            'fps_options': self.fps_options.get()
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

    def update_video(self):
        self.start_btn.configure(state=tk.DISABLED)
        self.fullscreen_btn.configure(state=tk.NORMAL)
        width = int(self.resolutions.get().split('x')[0])
        height = int(self.resolutions.get().split('x')[1])
        fps = int(self.fps_options.get())
        self.cap = fc.VideoCaptureCAM(selected_device, camsize_wh=(width, height), camfps=fps)
        ret, frame = self.cap.read()

        # Create a new window to display the video
        cv2.namedWindow(appname, cv2.WND_PROP_FULLSCREEN)
        cv2.resizeWindow(appname, width, height)
        if self.is_fullscreen:
            cv2.setWindowProperty(appname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        try:
            cv2.imshow(appname, frame)
        except Exception as e:
            messagebox.showerror("Error", "Error opening video source, try a lower resolution or frame rate option, your device may not support the selected resolution or frame rate.")
            self.cap.release()
            self.start_btn.configure(state=tk.NORMAL)
            self.fullscreen_btn.configure(state=tk.DISABLED)
            self.close_video_window()
            return
        prev_fullscreen_state = self.is_fullscreen
        while cv2.getWindowProperty(appname, cv2.WND_PROP_VISIBLE) >= 1:
            if self.cap is None:
                self.cap = fc.VideoCaptureCAM(selected_device, camsize_wh=(width, height), camfps=fps)
                if not self.cap.isOpened():
                    messagebox.showerror("Error", f"Error: Failed to open video device {selected_device}")
                    break
            
            if self.cap is not None:
                ret, frame = self.cap.read()
                if not ret or frame is None or frame.size == 0:
                    messagebox.showerror("Error", "Error: Could not read the frame")
                    self.cap.release()
                    self.cap = None
                else:
                    window_width = cv2.getWindowImageRect(appname)[2]
                    window_height = cv2.getWindowImageRect(appname)[3]
                    aspect_ratio = width / height
                    if window_width / window_height > aspect_ratio:
                        new_height = window_height
                        new_width = int(new_height * aspect_ratio)
                    else:
                        new_width = window_width
                        new_height = int(new_width / aspect_ratio)
                    frame = cv2.resize(frame, (new_width, new_height))
                    
                    # Add black borders to maintain aspect ratio
                    top_border = (window_height - new_height) // 2
                    bottom_border = window_height - new_height - top_border
                    left_border = (window_width - new_width) // 2
                    right_border = window_width - new_width - left_border
                    frame = cv2.copyMakeBorder(frame, top_border, bottom_border, left_border, right_border, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                    
                    cv2.imshow(appname, frame)
            
            # Detect if the window is in full screen mode
            if self.is_fullscreen != prev_fullscreen_state:
                self.cap.release()
                cv2.destroyAllWindows()
                cv2.namedWindow(appname, cv2.WND_PROP_FULLSCREEN)
                cv2.resizeWindow(appname, width, height)
                if self.is_fullscreen:
                    cv2.setWindowProperty(appname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                self.cap = fc.VideoCaptureCAM(selected_device, camsize_wh=(width, height), camfps=fps)
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size != 0:
                    cv2.imshow(appname, frame)
                prev_fullscreen_state = self.is_fullscreen
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # Escape key
                if self.cap is not None:
                    self.cap.release()
                    self.start_btn.configure(state=tk.NORMAL)
                    self.fullscreen_btn.configure(state=tk.DISABLED)
                cv2.destroyAllWindows()
                break
            elif key == ord('f'):  # F key
                self.toggle_fullscreen()
        
        self.start_btn.configure(state=tk.NORMAL)
        self.fullscreen_btn.configure(state=tk.DISABLED)
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
        # Create a new window with information about the application
        self.info_window = ctk.CTkToplevel(self.root)
        self.info_window.title("About")
        root.after(200, lambda: self.info_window.iconbitmap(icon_path))
        window_width = 250
        window_height = 200
        screen_width = self.root.winfo_screenwidth()
        x_position = int(screen_width / 2 - window_width / 2)
        y_position = 50
        self.info_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.info_window.resizable(False, False)
        info_text = (
            f"{appname} "
            "it's an application that allows you to view the video inputs available on your device.\n\n"
            f"Version: {version}\n"
            "Developed by: CesarGarza55"
        )
        
        info_label = ctk.CTkLabel(self.info_window, text=info_text, font=("Arial", 16), wraplength=window_width-35)
        info_label.pack(pady=20, padx=20)
        def open_link(event):
            webbrowser.open_new("https://github.com/CesarGarza55")

        link_label = ctk.CTkLabel(self.info_window, text="https://github.com/CesarGarza55", text_color="#0067ee", cursor="hand2", font=("Arial", 14, "underline"))
        link_label.pack(pady=10, padx=20)
        link_label.bind("<Button-1>", open_link)

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.lift()
            return
        # Create a new window with information about the application
        self.help_window = ctk.CTkToplevel(self.root)
        self.help_window.title("Help")
        root.after(200, lambda: self.help_window.iconbitmap(icon_path))
        window_width = 250
        window_height = 200
        screen_width = self.root.winfo_screenwidth()
        x_position = int(screen_width / 2 - window_width / 2)
        y_position = 50
        self.help_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.help_window.resizable(False, False)
        info_text = (
            "To start viewing the video input, select the video source and click the 'Start' button.\n\n"
            "If you want to view the video source in full screen, press the 'Fullscreen' button or press the 'F' key while the video window is open."
        )
        
        info_label = ctk.CTkLabel(self.help_window, text=info_text, font=("Arial", 16), wraplength=window_width-35)
        info_label.pack(pady=20, padx=20)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = VideoApp(root)
    root.mainloop()