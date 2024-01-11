import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import pickle
import tkinter as tk
import smtplib
import subprocess
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

path = 'training_images'
images = []
classNames = []
myList = os.listdir(path)
print(myList)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])
print(classNames)

# Load saved encodings if available, otherwise create and save them
encodings_file = 'encodings.pkl'
if os.path.exists(encodings_file):
    with open(encodings_file, 'rb') as f:
        encodeListKnown = pickle.load(f)
    print('Encodings loaded from file.')
else:
    encodeListKnown = []


    def findEncodings(images):
        encodeList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img, num_jitters=1)[0]
            encodeList.append(encode)
        return encodeList



    encodeListKnown = findEncodings(images)

    with open(encodings_file, 'wb') as f:
        pickle.dump(encodeListKnown, f)
    print('Encodings saved to file.')

print('Encoding Complete')



def start_external_script():
    script_path = 'add new person.py'  # Replace with the actual path to your script
    subprocess.Popen(['python', script_path])



def send_email():
    from_email = 'sarthakmalikmeerut@gmail.com'
    to_email = 'sarthakmalikmeerut@gmail.com'
    subject = 'Attendance Data'

    # Create the email message
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject

    # Attach the CSV file

    date_string = datetime.now().strftime('Hour-%H_Date-%d_Month-%m_Year-%y')
    filename = f'{date_string}.csv'
    attachment = open(filename, 'rb').read()
    attach_part = MIMEApplication(attachment, Name=filename)
    attach_part['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    message.attach(attach_part)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(from_email, 'mosy rpuz zyjo oyyw')  # Replace 'your_password' with your email password
        server.send_message(message)

    print('Email sent successfully.')



# Function to start attendance recognition
def start_attendance_recognition():
    print("Recognition started. Press 'Esc' to exit.")

    # Mark attendance only once
    attendance_marked = False

    # Counter to track consecutive frames with the same person
    consistent_frame_count = 0
    consistent_frame_threshold = 5  # Set the threshold as per your requirement

    while True:
        success, img = cap.read()
        # imgS = cv2.resize(img, (0,0), None, 0.25,0.25)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(img)
        encodesCurFrame = face_recognition.face_encodings(img, facesCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                # Check if the detected person is consistent for consecutive frames
                if consistent_frame_count >= consistent_frame_threshold:
                    if not attendance_marked:
                        mark_attendance(name)
                        attendance_marked = True
                    attendance_marked = False
                    consistent_frame_count = 0
                else:
                    consistent_frame_count += 1

            else:
                # Reset the counter if the person changes
                attendance_marked = False
                consistent_frame_count = 0

        cv2.imshow('Webcam', img)

        # Check for key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('e'):
            clear_attendance()

        # Break the loop if 'Esc' key is pressed
        elif key == 27:
            # Reset attendance_marked and consistent_frame_count when breaking the loop
            attendance_marked = False
            consistent_frame_count = 0
            break

# Function to mark attendance
def mark_attendance(name):
    now = datetime.now()
    date_string = now.strftime('Hour-%H_Date-%d_Month-%m_Year-%y')  # Include hour and minute in the filename
    file_name = f'{date_string}.csv'

    # Open the file in 'a+' mode (append and read)
    with open(file_name, 'a+') as f:
        # Move the file cursor to the beginning for reading
        f.seek(0)

        # Read all lines to check for existing names
        myDataList = f.readlines()

        # Check if the name is already in the file
        nameList = [line.split(',')[0] for line in myDataList]
        if name not in nameList:
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')
            print(f'Attendance marked for {name} at {dtString} on {date_string}.')


# Function to clear attendance
def clear_attendance():
    with open('Attendance.csv', 'w') as f:
        f.truncate(0)
    print('Attendance cleared.')

def start_recognition_thread():
    recognition_thread = threading.Thread(target=start_attendance_recognition)
    recognition_thread.start()

# Main loop
cap = cv2.VideoCapture(0)

# Create a Tkinter window
root = tk.Tk()
root.title("Attendance System")

# Create Tkinter buttons
start_button = tk.Button(root, text="Mark Attendance", command=start_recognition_thread())
start_button.pack(pady=10)

send_email_button = tk.Button(root, text="Send Email", command=send_email)
send_email_button.pack(pady=10)

external_script_button = tk.Button(root, text="Start External Script", command=start_external_script)
external_script_button.pack(pady=10)


# Main Tkinter loop
root.mainloop()

cap.release()
cv2.destroyAllWindows()

