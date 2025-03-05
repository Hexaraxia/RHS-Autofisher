import time
import pyautogui
import threading
import tkinter as tk
from tkinter import ttk
import psutil
import pygetwindow as gw
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
from comtypes import CLSCTX_ALL, CoInitialize, CoUninitialize
import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
import sv_ttk
import pywinstyles
import sys
import os
import warnings

warnings.simplefilter("ignore", wav.WavFileWarning)

running = False
peak_value_threshold = 0.01
last_sound_time = time.time()

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def normalize_audio(data):
    max_val = np.max(np.abs(data))
    return data / max_val if max_val > 0 else data

def play_splash_sound(peak_value):
    file_path = resource_path("splash.wav")
    samplerate, data = wav.read(file_path)
    normalized_data = normalize_audio(data)
    scaled_data = np.clip(normalized_data * peak_value, -1.0, 1.0)
    sd.play(scaled_data, samplerate)
    sd.wait()

def get_roblox_pid():
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if process.info['name'] == "RobloxPlayerBeta.exe":
            return process.info['pid']
    return None

def find_audio_session(pid):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.pid == pid:
            return session
    return None

def monitor_audio():
    global running, last_sound_time
    CoInitialize()
    try:
        pid = get_roblox_pid()
        if not pid:
            status_label.config(text="Roblox not found.")
            return
        session = find_audio_session(pid)
        if not session:
            status_label.config(text="Audio session not found for Roblox.")
            return
        audio_meter = session.SimpleAudioVolume.QueryInterface(IAudioMeterInformation)
        status_label.config(text="Monitoring Roblox audio...")
        while running:
            peak_value = audio_meter.GetPeakValue()
            if peak_value > peak_value_threshold:
                pyautogui.click()
                time.sleep(1.5)
                pyautogui.click()
                time.sleep(0.1)
                last_sound_time = time.time()
            elif time.time() - last_sound_time > 60:
                pyautogui.click()
                last_sound_time = time.time()
            time.sleep(0.1)
        status_label.config(text="Stopped monitoring.")
    finally:
        CoUninitialize()

def toggle_monitoring():
    global running
    running = not running
    toggle_button.config(text="Stop" if running else "Start")
    if running:
        threading.Thread(target=monitor_audio, daemon=True).start()
    else:
        status_label.config(text="Stopped.")

def check_roblox():
    status_label.config(text="Roblox found and connected." if get_roblox_pid() else "Roblox not found.")

def on_peak_value_input_change(event=None):
    global peak_value_threshold
    try:
        new_value = float(peak_value_input.get())
        peak_value_threshold = max(0.01, min(new_value, 1.0))
    except ValueError:
        pass
    peak_value_input.delete(0, tk.END)
    peak_value_input.insert(0, f"{peak_value_threshold:.2f}")
    peak_value_slider.set(peak_value_threshold)

def on_slider_value_change(val):
    global peak_value_threshold
    peak_value_threshold = float(val)
    if "peak_value_input" in globals():
        peak_value_input.delete(0, tk.END)
        peak_value_input.insert(0, f"{peak_value_threshold:.2f}")

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()
    if version.major == 10 and version.build >= 22000:
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

root = tk.Tk()
root.title("RHS Autofisher 2.0")
root.geometry("400x450")
root.iconbitmap(resource_path("icon.ico"))

sv_ttk.set_theme("dark")
apply_theme_to_titlebar(root)

window_width, window_height = 400, 450
screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
x_position, y_position = (screen_width // 2) - (window_width // 2), 50
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True, anchor="n")

title_label = ttk.Label(frame, text="RHS Autofisher 2.0", font=("Arial", 16, "bold"))
title_label.pack(pady=(0, 15), anchor="center")

toggle_button = ttk.Button(frame, text="Start", command=toggle_monitoring, width=20)
toggle_button.pack(pady=10)

volume_label = ttk.Label(frame, text="(Minimum Volume)")
volume_label.pack(pady=5, anchor="center")

peak_value_slider = ttk.Scale(frame, from_=0.01, to=1.0, orient="horizontal", command=on_slider_value_change)
peak_value_slider.set(peak_value_threshold)
peak_value_slider.pack(pady=5, anchor="center")

peak_value_input = ttk.Entry(frame, width=10, justify="center")
peak_value_input.insert(0, f"{peak_value_threshold:.2f}")
peak_value_input.pack(pady=5, anchor="center")
peak_value_input.bind("<FocusOut>", on_peak_value_input_change)

preview_button = ttk.Button(frame, text="Preview", command=lambda: play_splash_sound(peak_value_threshold), width=20)
preview_button.pack(pady=10)

check_button = ttk.Button(frame, text="Check for Roblox", command=check_roblox, width=20)
check_button.pack(pady=10)

status_label = ttk.Label(frame, text="Idle", font=("Arial", 10, "italic"))
status_label.pack(pady=10, anchor="center")

root.mainloop()
