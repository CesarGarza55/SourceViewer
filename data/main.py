import json, cv2, os, time, threading, pyaudio
import sys
import webbrowser
import unicodedata
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from pygrabber.dshow_graph import FilterGraph
import requests

# Application name and data path
version = "1.0.0"
appname = "SourceViewer"
appdata = os.environ["APPDATA"]
directory = os.path.join(appdata, appname)
user_data_path = os.path.join(directory, "settings.json")

script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "icon_app.ico")

try:
    response = requests.get("https://github.com/CesarGarza55/SourceViewer/releases/latest")
    response.raise_for_status()  # Verifica si la solicitud fue exitosa
    latest_release = response.json()
    latest_version = latest_release

    if latest_version > version:
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Update", "A new version is available. Would you like to download it?"):
            messagebox.showinfo("Download", "Please select the download location.")
            download_location = filedialog.askdirectory()
            if download_location:
                messagebox.showinfo("Download", "The download is in progress, please wait...")
                download_url = latest_release["assets"][0]["browser_download_url"]
                r = requests.get(download_url, allow_redirects=True)
                r.raise_for_status()  # Verifica si la descarga fue exitosa
                with open(os.path.join(download_location, f'{appname}-{latest_version}.exe'), 'wb') as f:
                    f.write(r.content)
                messagebox.showinfo("Download", "The download has been completed successfully.")
                sys.exit()
        root.destroy()
except requests.RequestException as e:
    print("Network error:", e)
except Exception as e:
    print("Error:", e)


if os.path.exists(f'{user_data_path}'):
    with open(f'{directory}/settings.json', 'r') as f:
        user_data = json.load(f)
        saved_video_source = int(user_data.get('video_source', 0))
        saved_audio_source = int(user_data.get('audio_source', 0))
else:
    os.makedirs(f'{directory}', exist_ok=True)
    with open(user_data_path, 'w') as f:
        data = {
            "video_source": "0",
            "audio_source": "0"
        }
        json.dump(data, f)
        saved_video_source = 0
        saved_audio_source = 0

class VideoApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{appname} - Settings")
        window_width = 300
        window_height = 300
        x_position = 50
        y_position = 50
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.resizable(False, False)
        self.root.iconbitmap(icon_path)

        # Variables
        global saved_video_source, saved_audio_source
        self.video_source = saved_video_source
        self.audio_source = saved_audio_source
        self.is_fullscreen = False
        self.cap = None
        self.audio_stream = None
        self.audio_output_stream = None
        self.video_window = None
        self.video_thread = None
        self.audio_thread = None
        self.stop_threads = threading.Event()
        
        # Frame for controls in the main window
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill=ctk.BOTH, expand=True)

        # Combobox to select the video source
        self.video_sources = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.video_sources.pack(pady=(40, 10), fill=ctk.BOTH, expand=True)

        # Combobox to select the audio source
        self.audio_sources = ctk.CTkComboBox(self.control_frame, state="readonly", command=lambda x: self.save_settings())
        self.audio_sources.pack(pady=10, fill=ctk.BOTH, expand=True)

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

        # Title label
        self.title_label = ctk.CTkLabel(self.control_frame, text="Visualize your video and audio sources")
        self.title_label.place(relx=0.0, rely=0.0, anchor="nw", x=5, y=5)

        # Detect available video and audio sources
        self.detect_video_sources()
        self.detect_audio_sources()

    def save_settings(self):
        global saved_video_source, saved_audio_source
        video_source = self.video_sources.get().split()
        audio_source = self.audio_sources.get().split()
        if len(video_source) > 1:
            saved_video_source = video_source[1].replace(':', '')
        if len(audio_source) > 1:
            saved_audio_source = audio_source[1].replace(':', '')
        os.makedirs(f'{directory}', exist_ok=True)
        # Save the data to a file
        data = {
            'video_source': saved_video_source,
            'audio_source': saved_audio_source
        }
        # Save data to a file
        with open(f'{user_data_path}', 'w') as f:
            json.dump(data, f)

    def detect_video_sources(self):
        graph = FilterGraph()
        devices = graph.get_input_devices()
        sources = [f"Source {i}: {device}" for i, device in enumerate(devices)]
        self.video_sources.configure(values=sources)
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
                if name not in seen_device_names and not self.is_virtual_device(name):
                    seen_device_names.add(name)
                    source_name = f"Source {id}: {name}"
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

    def set_audio_source(self, source):
        if self.audio_stream is not None:
            if self.audio_stream.is_active():
                self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.audio_output_stream is not None:
            if self.audio_output_stream.is_active():
                self.audio_output_stream.stop_stream()
            self.audio_output_stream.close()
        p = pyaudio.PyAudio()
        device_info = p.get_device_info_by_index(source)
        max_sample_rate = device_info['defaultSampleRate']
        self.audio_stream = p.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=int(max_sample_rate),
                                input=True,
                                input_device_index=source,
                                frames_per_buffer=4096)

        # Setting up the audio output stream
        self.audio_output_stream = p.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=int(max_sample_rate),
                                        output=True)

    def set_video_source(self, source):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(source)

    def change_video_source(self, event):
        selected_source = self.video_sources.get()
        self.video_source = int(selected_source.split()[1].replace(':', ''))

    def open_video_window(self):
        # Make sure the video and audio source are updated before opening the video window
        self.change_video_source(None)
        self.change_audio_source(None)
        
        if self.video_window is None or not self.video_window.winfo_exists():
            self.video_window = ctk.CTkToplevel(self.root)
            self.video_window.title(f"{appname} - Video Viewer")
            root.after(200, lambda: self.video_window.iconbitmap(icon_path))
            window_width = 800
            window_height = 600
            x_position = 500
            y_position = 50
            self.video_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
            self.video_window.protocol("WM_DELETE_WINDOW", self.close_video_window)
            self.fullscreen_btn.configure(state=ctk.NORMAL)
            self.start_btn.configure(text="Stop")
            self.start_btn.configure(fg_color="red", hover_color="darkred")
            self.start_btn.configure(command=self.close_video_window)

            # Bind F11 key to toggle full screen
            self.video_window.bind("<F11>", self.toggle_fullscreen_event)

            # Frame for the video
            self.video_frame = ctk.CTkFrame(self.video_window, fg_color="black")
            self.video_frame.pack(fill=ctk.BOTH, expand=True)
            self.video_label = ctk.CTkLabel(self.video_frame, text="")
            self.video_label.pack(fill=ctk.BOTH, expand=True)

            # Setting up video and audio capture
            self.set_video_source(self.video_source)
            self.set_audio_source(self.audio_source)

            # Start capturing video and audio in separate threads
            self.stop_threads.clear()
            self.video_thread = threading.Thread(target=self.update_video, daemon=True)
            self.audio_thread = threading.Thread(target=self.update_audio, daemon=True)
            self.video_thread.start()
            self.audio_thread.start()

    def update_video(self):
        while not self.stop_threads.is_set():
            if self.cap and self.cap.isOpened():
                try:
                    ret, frame = self.cap.read()
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame)

                        # Get window dimensions
                        window_width = self.video_window.winfo_width()
                        window_height = self.video_window.winfo_height()

                        # Calculate image size while maintaining aspect ratio
                        img_width, img_height = img.size
                        ratio = min(window_width / img_width, window_height / img_height)
                        new_width = int(img_width * ratio)
                        new_height = int(img_height * ratio)

                        # Verify that the new dimensions are valid
                        if new_width > 0 and new_height > 0:
                            img = img.resize((new_width, new_height), Image.NEAREST)
                        else:
                            new_width, new_height = img_width, img_height

                        ctk_img = ctk.CTkImage(light_image=img, size=(new_width, new_height))
                        self.root.after(0, self.update_image, ctk_img)
                except Exception as e:
                    print(f"Error en la actualización del video: {e}")
                    break
            time.sleep(0.01)  # Add a small delay to avoid high CPU load

    def update_image(self, ctk_img):
        if self.video_window and self.video_window.winfo_exists():
            self.video_label.configure(image=ctk_img)

    def update_audio(self):
        while not self.stop_threads.is_set():
            if self.audio_stream and self.audio_stream.is_active():
                try:
                    data = self.audio_stream.read(4096, exception_on_overflow=False) # Read more data with a larger buffer
                    # Play the captured audio
                    self.audio_output_stream.write(data)
                except IOError:
                    continue

    def toggle_fullscreen(self):
        if self.video_window:
            self.is_fullscreen = not self.is_fullscreen
            self.video_window.attributes("-fullscreen", self.is_fullscreen)
            if not self.is_fullscreen:
                self.video_window.geometry("800x600")

    def toggle_fullscreen_event(self, event):
        self.toggle_fullscreen()

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
        if self.video_thread:
            self.video_thread.join(timeout=1)
        if self.audio_thread:
            self.audio_thread.join(timeout=1)
        self.close_audio_stream()  # Cerrar los streams de audio
        if self.cap:
            self.cap.release()
        if self.video_window:
            self.video_window.destroy()
            self.video_window = None
        self.start_btn.configure(text="Start")
        self.start_btn.configure(command=self.open_video_window)
        self.start_btn.configure(fg_color="green", hover_color="darkgreen")
        self.fullscreen_btn.configure(state=ctk.DISABLED)

    def close_window(self):
        self.stop_threads.set()
        if self.video_thread:
            self.video_thread.join(timeout=1)
        if self.audio_thread:
            self.audio_thread.join(timeout=1)
        self.close_audio_stream()  # Cerrar los streams de audio
        if self.cap:
            self.cap.release()
        if self.video_window:
            self.video_window.destroy()
        self.root.destroy()

    def show_info(self):
        info_window = ctk.CTkToplevel(self.root)
        info_window.title("About")
        root.after(200, lambda: info_window.iconbitmap(icon_path))
        window_width = 250
        window_height = 200
        screen_width = self.root.winfo_screenwidth()
        x_position = int(screen_width / 2 - window_width / 2)
        y_position = 50
        info_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        info_window.resizable(False, False)
        info_text = (
            f"{appname} "
            "it's an application that allows you to view the video inputs available on your device.\n\n"
            f"Version: {version}\n"
            "Developed by: CesarGarza55"
        )
        
        info_label = ctk.CTkLabel(info_window, text=info_text, font=("Arial", 16), wraplength=window_width-35)
        info_label.pack(pady=20, padx=20)
        def open_link(event):
            webbrowser.open_new("https://github.com/CesarGarza55")
    
        link_label = ctk.CTkLabel(info_window, text="https://github.com/CesarGarza55", text_color="#0067ee", cursor="hand2", font=("Arial", 14, "underline"))
        link_label.pack(pady=10, padx=20)
        link_label.bind("<Button-1>", open_link)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    app = VideoApp(root)
    root.mainloop()