import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime

class CameraApp:
    def __init__(self, window, window_title, video_source=0):
        self.window = window
        self.window.title(window_title)

        self.video_source = video_source
        self.cap = cv2.VideoCapture(self.video_source)

        self.canvas = tk.Canvas(window, width=self.cap.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        self.btn_capture = ttk.Button(window, text="Capture", command=self.capture_image)
        self.btn_capture.pack(pady=10)

        self.update()
        self.window.mainloop()

    def update(self):
        ret, frame = self.cap.read()
        if ret:
            self.photo = self.convert_to_tkinter_image(frame)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.window.after(10, self.update)

    def capture_image(self):
        ret, frame = self.cap.read()
        if ret:
            file_name = input()
            cv2.imwrite(file_name, frame)
            print(f"Image captured and saved as {file_name}")

    def convert_to_tkinter_image(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        photo = ImageTk.PhotoImage(image=pil_image)
        return photo

    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    # Specify the video source (use 0 for the default camera)
    video_source = 0

    # Create the application window
    app_window = tk.Tk()
    app = CameraApp(app_window, "Camera App", video_source)
