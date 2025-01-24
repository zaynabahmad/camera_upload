import cv2
import boto3
import os
from flask import Flask, render_template, Response
import threading
import time
from datetime import datetime

app = Flask(__name__)

# AWS S3 configuration
AWS_ACCESS_KEY = "your-access-key"
AWS_SECRET_KEY = "your-secret-key"
BUCKET_NAME = "your-s3-bucket-name"
FOLDER_NAME = "raspberry-camera-images"

# Initialize S3 client
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

# Global variables
output_frame = None
lock = threading.Lock()

# Initialize the Raspberry Pi camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Set width
cap.set(4, 480)  # Set height

def capture_and_upload():
    global output_frame, lock
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        # Lock the frame for thread-safe access
        with lock:
            output_frame = frame

        # Save the frame as an image file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"image_{timestamp}.jpg"
        local_path = f"/tmp/{image_filename}"

        # Save locally
        cv2.imwrite(local_path, frame)
        print(f"Image saved locally: {local_path}")

        # Upload to S3
        try:
            s3.upload_file(local_path, BUCKET_NAME, f"{FOLDER_NAME}/{image_filename}")
            print(f"Uploaded {image_filename} to S3")
        except Exception as e:
            print(f"Failed to upload {image_filename} to S3: {e}")

        # Remove the local file to save space
        if os.path.exists(local_path):
            os.remove(local_path)

        # Sleep to control the upload interval (e.g., one image every 10 seconds)
        time.sleep(10)

def generate():
    global output_frame, lock
    while True:
        if output_frame is not None:
            with lock:
                # Encode the frame as JPEG
                ret, jpeg = cv2.imencode('.jpg', output_frame)
                if ret:
                    frame = jpeg.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start the capture and upload thread
    capture_thread = threading.Thread(target=capture_and_upload)
    capture_thread.daemon = True
    capture_thread.start()

    # Start the Flask app
    app.run(host='0.0.0.0', port=8080, debug=False)
