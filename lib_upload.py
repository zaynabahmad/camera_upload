import boto3
import os
import subprocess
from flask import Flask, render_template, Response
import threading
import time
from datetime import datetime

app = Flask(__name__)

# AWS S3 configuration
AWS_ACCESS_KEY = "AKIARWPFIGTLOJITWPXH"
AWS_SECRET_KEY = "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"
BUCKET_NAME = "camera-imagess"
FOLDER_NAME = "raspberry-camera-images"

# Initialize S3 client
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

# Local directory to save images
local_folder = "/home/pi/captured_images"
os.makedirs(local_folder, exist_ok=True)  # Create the directory if it doesn't exist

def capture_and_upload():
    while True:
        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"image_{timestamp}.jpg"
        local_path = os.path.join(local_folder, image_filename)

        # Capture an image using libcamera
        try:
            # Use libcamera-still to capture an image
            command = f"libcamera-still -o {local_path}"
            subprocess.run(command, shell=True, check=True)
            print(f"[INFO] Image captured and saved locally: {local_path}")
        except Exception as e:
            print(f"[ERROR] Failed to capture image: {e}")
            continue  # Skip to the next iteration

        # Upload the image to S3
        print(f"[INFO] Uploading image to S3...")
        try:
            s3.upload_file(local_path, BUCKET_NAME, f"{FOLDER_NAME}/{image_filename}")
            print(f"[INFO] Image uploaded to S3: {image_filename}")
        except Exception as e:
            print(f"[ERROR] Failed to upload image to S3: {e}")

        # Optionally delete the local image after uploading
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"[INFO] Local image deleted: {local_path}")

        # Sleep for 2 seconds before capturing the next image
        time.sleep(2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response("Streaming not implemented yet", mimetype='text/plain')

if __name__ == '__main__':
    # Start the capture and upload thread
    capture_thread = threading.Thread(target=capture_and_upload)
    capture_thread.daemon = True
    capture_thread.start()

    # Start the Flask app
    app.run(host='0.0.0.0', port=8080, debug=False)
