
import cv2
import numpy as np
import face_recognition
import os
import pickle
from datetime import datetime
import csv
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, Response, request, redirect, url_for
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

app = Flask(__name__)
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
cap = None
attendance = {}



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




def start_camera():
    global cap
    cap = cv2.VideoCapture(0)


def stop_camera():
    global cap
    if cap is not None:
        cap.release()
        cap = None


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

def generate_frames():
    while True:
        if cap is not None:
            success, img = cap.read()
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
                    mark_attendance(name)

            ret, frame = cv2.imencode('.jpg', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            frame = frame.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    path = 'training_images'
    classNames = [os.path.splitext(cl)[0] for cl in os.listdir(path)]
    return render_template('index.html',classNames=classNames)
    print(request.headers)
    print(request.get_data(as_text=True))


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_recognition', methods=['POST'])
def start_recognition_route():
    start_camera()
    return render_template('index.html')

@app.route('/send_email', methods=['POST'])
def send_email_route():
    if cap is not None:
        stop_camera()  # Stop the camera before sending the email

    # Create a new CSV file for the current time (if not already created)
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    hour = now.hour
    file_name = f'{date_string}_{hour}.csv'
    if not os.path.exists(file_name):
        with open(file_name, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Date', 'Timestamp'])

    # Send email with the current CSV file
    send_email(file_name)

    return render_template('index.html')


@app.route('/add_person', methods=['POST'])
def add_person_route():
    if request.method == 'POST':
        person_name = request.form.get('personName')

        # Initialize video capture
        cap = cv2.VideoCapture(0)

        # Capture a few frames to allow the user to position their face
        for _ in range(5):
            _, frame = cap.read()

        # Convert the frame to RGB format
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Find face locations in the frame
        face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            # No face found, handle this case as needed
            return redirect(url_for('index'))

        # Take the first face found (assuming only one person is present)
        top, right, bottom, left = face_locations[0]

        # Crop the face from the frame
        face_image = frame[top:bottom, left:right]

        # Save the face image to the 'training_images' folder
        save_path = os.path.join('training_images', f'{person_name}.jpg')
        cv2.imwrite(save_path, cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))



        os.remove("encodings.pkl")

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

        encodeListKnown = []
        for image in images:
            face_encodings = face_recognition.face_encodings(image)
            if len(face_encodings) > 0:
                encodeListKnown.append(face_encodings[0])
            with open(encodings_file, 'wb') as f:
                pickle.dump(encodeListKnown, f)
        print('Encodings saved to file.')


        cap.release()

        return redirect(url_for('index'))


@app.route('/remove_person', methods=['POST'])
def remove_person_route():
    encodings_file = 'encodings.pkl'
    if request.method == 'POST':
        person_to_remove = request.form.get('removePersonName')

        os.remove(f"training_images/{person_to_remove}.jpg")
        os.remove(encodings_file)
        # Load existing encodings

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

        encodeListKnown = []
        for image in images:
            face_encodings = face_recognition.face_encodings(image)
            if len(face_encodings) > 0:
                encodeListKnown.append(face_encodings[0])
            with open(encodings_file, 'wb') as f:
                pickle.dump(encodeListKnown, f)
        print('Encodings saved to file.')





        # Find the index of the person to remove
        index_to_remove = None
        for i, name in enumerate(classNames):
            if name == person_to_remove:
                index_to_remove = i
                break

        if index_to_remove is not None:
            # Remove the person's encoding and name
            del encodeListKnown[index_to_remove]
            del classNames[index_to_remove]

            # Save the updated encodings list
            with open(encodings_file, 'wb') as f:
                pickle.dump(encodeListKnown, f)

            return redirect(url_for('index'))
        else:
            # Handle the case where the person to remove is not found
            return render_template('index.html', error_message="Person not found in the dataset.")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
