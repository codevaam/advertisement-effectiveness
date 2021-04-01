from app import app
import numpy as np
import cv2
from flask import render_template, Response

camera = cv2.VideoCapture(0)

@app.route("/")
def index():
    return "hello"

def gen_frames():
    while(True):
        sucess, frame = camera.read()
        if not sucess:
            break

        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route("/home")
def home():
    return render_template('index.html')

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# When everything done, release the capture
# cap.release()
# cv2.destroyAllWindows()