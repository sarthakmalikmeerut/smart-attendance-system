import cv2
import speech_recognition as sr
import numpy as np
import face_recognition
import os
from datetime import datetime
import pickle

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


recognizer = sr.Recognizer()
microphone = sr.Microphone()
# ... (previous code)

def start_listening():
    with microphone as source:
        print("Say 'Mark Attendance' to start recognition...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio).lower()
        print(f"Command: {command}")
        return "mark attendance" in command
    except sr.UnknownValueError:
        return False
    except sr.RequestError as e:
        print(f"Speech Recognition request failed: {e}")
        return False

cap = cv2.VideoCapture(1)

def markAttendance(name):
    now = datetime.now()
    date_string = now.strftime('%d_%m_%y_%H%M')  # Include hour and minute in the filename
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

def clearAttendance():
    with open('Attendance.csv', 'w') as f:
        f.truncate(0)
    print('Attendance cleared.')

# Main Loop
# ... (previous code)

# ... (previous code)

# Main Loop
while True:
    # Start listening for the command
    if start_listening():
        print("Recognition started. Press 'Esc' to exit.")

        # Mark attendance only once
        attendance_marked = False

        # Counter to track consecutive frames with the same person
        consistent_frame_count = 0
        consistent_frame_threshold = 5  # Set the threshold as per your requirement

        while True:
            success, img = cap.read()
            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

            facesCurFrame = face_recognition.face_locations(imgS)
            encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

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
                            markAttendance(name)
                            attendance_marked = True
                        attendance_marked= False
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
                clearAttendance()

            # Break the loop if 'Esc' key is pressed
            elif key == 27:
                # Reset attendance_marked and consistent_frame_count when breaking the loop
                attendance_marked = False
                consistent_frame_count = 0
                break

    else:
        print("Recognition not started. Press 'Esc' to exit.")

    # Check for key press outside the attendance recognition loop
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
