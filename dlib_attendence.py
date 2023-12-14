# import cv2
# import numpy as np
# import face_recognition
# import os
# from datetime import datetime
#
# path = 'training_images'
# images = []
# classNames = []
# myList = os.listdir(path)
# print(myList)
# for cl in myList:
#     curImg = cv2.imread(f'{path}/{cl}')
#     images.append(curImg)
#     classNames.append(os.path.splitext(cl)[0])
# print(classNames)
#
#
# def findEncodings(images):
#     encodeList = []
#
#     for img in images:
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#         encode = face_recognition.face_encodings(img)[0]
#         encodeList.append(encode)
#     return encodeList
#
#
# def markAttendance(name):
#     with open('Attendance.csv', 'r+') as f:
#         myDataList = f.readlines()
#
#         nameList = [line.split(',')[0] for line in myDataList]
#         if name not in nameList:
#             now = datetime.now()
#             dtString = now.strftime('%H:%M:%S')
#             f.writelines(f'\n{name},{dtString}')
#             print(f'Attendance marked for {name} at {dtString}')
#         else:
#             pass
#
#
# def clearAttendance():
#     with open('Attendance.csv', 'w') as f:
#         f.truncate(0)
#     print('Attendance cleared.')
#
#
# encodeListKnown = findEncodings(images)
# print('Encoding Complete')
#
# cap = cv2.VideoCapture(1)
#
# while True:
#     success, img = cap.read()
#     imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
#     imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
#
#     facesCurFrame = face_recognition.face_locations(imgS)
#     encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
#
#     for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
#         matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
#         faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
#         matchIndex = np.argmin(faceDis)
#
#         if matches[matchIndex]:
#             name = classNames[matchIndex].upper()
#             y1, x2, y2, x1 = faceLoc
#             y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
#             cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
#             cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
#             markAttendance(name)
#
#     cv2.imshow('Webcam', img)
#
#     # Check for key press
#     key = cv2.waitKey(1) & 0xFF
#     if key == ord('e'):
#         clearAttendance()
#
#     # Break the loop if 'Esc' key is pressed
#     elif key == 27:
#         break
#
# cap.release()
# cv2.destroyAllWindows()

import cv2
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
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList


    encodeListKnown = findEncodings(images)

    with open(encodings_file, 'wb') as f:
        pickle.dump(encodeListKnown, f)
    print('Encodings saved to file.')

print('Encoding Complete')

cap = cv2.VideoCapture(1)

def markAttendance(name):
    with open('Attendance.csv', 'r+') as f:
        myDataList = f.readlines()

        nameList = [line.split(',')[0] for line in myDataList]
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')
            print(f'Attendance marked for {name} at {dtString}')
        else:
            pass

def clearAttendance():
    with open('Attendance.csv', 'w') as f:
        f.truncate(0)
    print('Attendance cleared.')

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
            markAttendance(name)

    cv2.imshow('Webcam', img)

    # Check for key press
    key = cv2.waitKey(1) & 0xFF
    if key == ord('e'):
        clearAttendance()

    # Break the loop if 'Esc' key is pressed
    elif key == 27:
        break

cap.release()
cv2.destroyAllWindows()

