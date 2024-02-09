import cv2
import face_recognition
import os
import pickle
from datetime import datetime
import csv
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
from email.mime.text import MIMEText


# Load images and class names
path = 'training_images'
images = [cv2.imread(f'{path}/{cl}') for cl in os.listdir(path)]
classNames = [os.path.splitext(cl)[0] for cl in os.listdir(path)]

# Load or create encodings
encodings_file = 'encodings.pkl'
encodeListKnown = []

if os.path.exists(encodings_file):
    with open(encodings_file, 'rb') as f:
        encodeListKnown = pickle.load(f)

# Initialize video capture
cap = cv2.VideoCapture(0)
attendance = {}


def release_camera():
    global cap
    if cap is not None:
        cap.release()



def mark_attendance(name):
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    hour = now.hour
    file_name = f'{date_string}_{hour}.csv'

    if name not in attendance:
        attendance[name] = set()

    if hour not in attendance[name]:
        attendance[name].add(hour)

        # Check if the CSV file for the current hour and date already exists
        if not os.path.exists(file_name):
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Name', 'Date', 'Timestamp'])

        # Check if the name and timestamp combination already exists in the CSV file
        with open(file_name, mode='r', newline='') as file:
            reader = csv.reader(file)
            existing_entries = set((row[0], row[2]) for row in reader)

        if (name, str(hour)) not in existing_entries:
            with open(file_name, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([name, date_string, str(hour)])
                print(f"Attendance marked for {name} at {hour}:00")
        else:
            print(f"Attendance already marked for {name} at {hour}:00")

def remove_person(selected_person):
    global encodeListKnown
    if selected_person:
        try:
            index_to_remove = classNames.index(selected_person)
            del encodeListKnown[index_to_remove]
            classNames.remove(selected_person)
            os.remove(f"training_images/{selected_person}.jpg")
            messagebox.showinfo("Success", f"{selected_person} removed successfully!")
        except ValueError:
            messagebox.showerror("Error", f"{selected_person} not found!")

def open_camera():
    global cap, encodeListKnown

    release_camera()

    cap = cv2.VideoCapture(0)

    def update_frame():
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)

        for encode_face, face_loc in zip(encodes_cur_frame, faces_cur_frame):
            face_dis = face_recognition.face_distance(encodeListKnown, encode_face)
            match_index = np.argmin(face_dis)
            confidence = 1 - face_dis[match_index]  # Invert the distance value for confidence

            if face_dis[match_index] < 0.5:  # You can adjust this threshold based on your requirements
                name = classNames[match_index].upper()
                y1, x2, y2, x1 = face_loc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, f"{name} ({confidence:.2f})", (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                mark_attendance(name)

        img = Image.fromarray(frame)
        img = ImageTk.PhotoImage(img)
        panel.img = img
        panel.config(image=img)
        root.after(10, update_frame)

    update_frame()



def send_email(file_path):
    sender_email = "sarthakmalikmeerut@gmail.com"  # Replace with your email
    sender_password = "nmbc bybf dhng kdsg"
    receiver_email = "sarthakmalikmeerut@gmail.com"  # Replace with the recipient's email

    subject = "Attendance CSV File"
    body = "Please find the attached attendance CSV file."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with open(file_path, "rb") as file:
        attachment = MIMEApplication(file.read(), _subtype="csv")
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(file_path))
        message.attach(attachment)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:  # Use your email provider's SMTP details
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())



root = tk.Tk()
root.title("Attendance System")

button_mark_attendance = ttk.Button(root, text="Mark Attendance", command=open_camera)
button_mark_attendance.pack(pady=10)


def start_script1():
    release_camera()
    subprocess.run(['python', 'add new person.py'])

def start_script2():
    release_camera()
    subprocess.run(['python', 'remove person.py'])

def send_email_button():
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    hour = now.hour
    file_name = f'{date_string}_{hour}.csv'

    if os.path.exists(file_name):
        send_email(file_name)
        messagebox.showinfo("Email Sent", f"Attendance CSV file sent successfully!")
    else:
        messagebox.showerror("Error", "Attendance CSV file not found!")


# Create buttons for starting external scripts
button_start_script1 = ttk.Button(root, text="add new person", command=start_script1)
button_start_script1.pack(pady=5)

button_start_script2 = ttk.Button(root, text="remove existing person", command=start_script2)
button_start_script2.pack(pady=5)

button_send_email = ttk.Button(root, text="Send Email", command=send_email_button)
button_send_email.pack(pady=10)


# Define panel outside the open_camera function
panel = tk.Label(root)
panel.pack(padx=10, pady=10)

root.mainloop()

# Release the video capture when the Tkinter window is closed
cap.release()
