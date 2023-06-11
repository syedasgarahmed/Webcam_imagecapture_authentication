import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import ImageTk, Image
import threading
import os
import random
import string
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from urllib.request import Request

# Initialize the camera
camera = None
preview_thread = None
otp_entry_state = "disabled"
sent_otp = None

def generate_otp(length=6):
    """Generate a random OTP of the specified length."""
    digits = string.digits
    otp = ''.join(random.choice(digits) for _ in range(length))
    return otp

def send_otp_email(recipient_email):
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request(os.environ['REFRESH_TOKEN']))
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    otp = generate_otp()  # Generate random OTP
    message = create_message("me", recipient_email, "OTP Verification", f"Your OTP is: {otp}")
    send_message(service, "me", message)

    return otp


def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('OTP sent successfully.')
    except Exception as e:
        print('Error sending OTP:', e)

def start_camera():
    global camera, preview_thread, otp_entry_state, sent_otp
    camera = cv2.VideoCapture(0)
    messagebox.showinfo("Camera", "Camera started")
    sent_otp = send_otp_email("your_email@gmail.com")  # Update recipient email
    messagebox.showinfo("OTP", "OTP sent to your email")
    preview_thread = threading.Thread(target=update_preview)
    preview_thread.start()
    otp_entry.config(state="normal")
    otp_entry_state = "normal"

def capture_image():
    global camera
    ret, frame = camera.read()
    if ret:
        cv2.imwrite("captured_image.jpg", frame)
        messagebox.showinfo("Capture", "Image captured")
    else:
        messagebox.showwarning("Capture", "Failed to capture image")

def stop_camera():
    global camera, preview_thread, otp_entry_state
    if camera is not None:
        camera.release()
        messagebox.showinfo("Camera", "Camera stopped")
        preview_thread.join()
        otp_entry.config(state="disabled")
        otp_entry_state = "disabled"
    else:
        messagebox.showwarning("Camera", "Camera not started")

def submit_otp():
    otp = otp_entry.get()
    if otp == sent_otp:
        messagebox.showinfo("OTP", "OTP successful")
    else:
        messagebox.showwarning("OTP", "OTP incorrect")

def update_preview():
    global camera
    if camera is not None:
        ret, frame = camera.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img = img.resize((640, 480), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=img)
            canvas.imgtk = imgtk
            canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        window.after(10, update_preview)

# Create the main window
window = tk.Tk()
window.title("Camera App")

# Create the canvas for camera preview
canvas = tk.Canvas(window, width=640, height=480)
canvas.pack()

# Create the start camera button
start_button = tk.Button(window, text="Start Camera", command=start_camera)
start_button.pack()

# Create the capture image button
capture_button = tk.Button(window, text="Capture Image", command=capture_image)
capture_button.pack()

# Create the stop camera button
stop_button = tk.Button(window, text="Stop Camera", command=stop_camera)
stop_button.pack()

# Create the OTP label and entry
otp_label = tk.Label(window, text="Enter OTP:")
otp_label.pack()

otp_entry = tk.Entry(window, state=otp_entry_state)
otp_entry.pack()

# Create the submit OTP button
submit_button = tk.Button(window, text="Submit OTP", command=submit_otp)
submit_button.pack()

# Run the GUI main loop
window.mainloop()
