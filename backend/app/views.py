from app import app
import numpy as np
import cv2
from flask import render_template, Response, request, jsonify, redirect, url_for
import dlib
import pymongo

from bson.json_util import dumps
from bson import json_util

cap = cv2.VideoCapture(cv2.CAP_V4L2)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
center_count = []


mongo_connection = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = mongo_connection["AdSurvey"]
users = mydb["users"]


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/admin", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("companyLogin.html")

    if request.method == "POST":
        print(request.json)
        return redirect(url_for("companyAnalysis"))


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if request.method == "GET":
        return render_template("survey.html")

    if request.method == "POST":
        data = request.json
        print(request.json)
        print(type(center_count))
        attention = center_count.count(1)/len(center_count)
        data["attention"] = center_count.count(1)/len(center_count)
        print(data)
        x = users.insert_one(data)

        res = {'attention': attention}
        # region = data.get("region")
        # age = int(data.get("age"))
        # play_head = data.get("playhead")
        # is_skipped = data.get("skipped")
        return jsonify(res)


@app.route("/instructions")
def instructions():
    return render_template("instructions.html")


@app.route("/analysis", methods=["GET"])
def analysis():
    skip_count = users.count_documents({"skipped": "true"})
    total_count = users.count_documents({})

    pieData = []
    pieData.append(skip_count)
    pieData.append(total_count-skip_count)

    print(skip_count)
    return render_template("analysis.html", data=pieData)


@app.route("/companyAnalysis", methods=["GET"])
def companyAnalysis():
    skip_count = users.count_documents({"skipped": "true"})
    total_count = users.count_documents({})

    pieData = []
    pieData.append(skip_count)
    pieData.append(total_count-skip_count)

    allUsers = users.find({})
    json_data = dumps(list(allUsers))

    return render_template("companyAnalysis.html", data=pieData, users=json_data)


def midpoint(p1, p2):
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)


def get_gaze_ratio(eye_points, facial_landmarks, frame, gray):

    # getting the eye region using dlib library
    eye_region = np.array([(facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y),
                           (facial_landmarks.part(eye_points[1]).x, facial_landmarks.part(
                               eye_points[1]).y),
                           (facial_landmarks.part(eye_points[2]).x, facial_landmarks.part(
                               eye_points[2]).y),
                           (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(
                               eye_points[3]).y),
                           (facial_landmarks.part(eye_points[4]).x, facial_landmarks.part(
                               eye_points[4]).y),
                           (facial_landmarks.part(eye_points[5]).x, facial_landmarks.part(eye_points[5]).y)], np.int32)
    height, width, _ = frame.shape

    # creating mask with the same dimention as the frame
    mask = np.zeros((height, width), np.uint8)

    # changing pixel values of the mask with the eye region to 255
    cv2.polylines(mask, [eye_region], True, 255, 2)
    cv2.fillPoly(mask, [eye_region], 255)

    # using bitwise and opteration getting eye region from input stream
    eye = cv2.bitwise_and(gray, gray, mask=mask)

    # using min and max values of x and y values getting the eye region coordinates
    min_x = np.min(eye_region[:, 0])
    max_x = np.max(eye_region[:, 0])

    min_y = np.min(eye_region[:, 1])
    max_y = np.max(eye_region[:, 1])

    # apply simple threasholding to the grayscale eye image with value 70
    gray_eye = eye[min_y: max_y, min_x: max_x]

    # cv2.imshow("gray eye", gray_eye)
    _, threshold_eye = cv2.threshold(
        gray_eye, 70, 255, cv2.THRESH_BINARY)

    threshold_eye = cv2.resize(threshold_eye, None, fx=5, fy=5)

    # getting height of threshold eye and thresholding left/right side
    t_height, t_width = threshold_eye.shape
    left_side_threshold = threshold_eye[0:t_height, 0: int(t_width/2)]
    right_side_threshold = threshold_eye[0:t_height, int(
        t_width/2): t_width]

    # calculating white pixels on left and right threshold
    left_side_white = cv2.countNonZero(left_side_threshold)
    right_side_white = cv2.countNonZero(right_side_threshold)

    eye = cv2.resize(eye, None, fx=5, fy=5)
    cv2.imshow("threshold", threshold_eye)
    cv2.imshow("mask", mask)
    # cv2.imshow("eye", eye)
    if(right_side_white != 0):
        gaze_ratio = left_side_white/right_side_white
        return gaze_ratio
    else:
        return 0.95


def gen_frames():
    while True:
        _, frame = cap.read()
        # if(frame is not None):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector(gray)
        for face in faces:
            # x, y = face.left(), face.top()
            # x1, y1 = face.right(), face.bottom()
            # cv2.rectangle(frame, (x, y), (x1, y1), (0, 255, 0), 2)

            landmarks = predictor(gray, face)
            left_point = (landmarks.part(36).x, landmarks.part(36).y)
            right_point = (landmarks.part(39).x, landmarks.part(39).y)
            center_top = midpoint(landmarks.part(37), landmarks.part(38))
            center_bottom = midpoint(landmarks.part(41), landmarks.part(40))

            gaze_ratio_left_eye = get_gaze_ratio(
                [36, 37, 38, 39, 40, 41], landmarks, frame, gray)
            gaze_ratio_right_eye = get_gaze_ratio(
                [42, 43, 44, 45, 46, 47], landmarks, frame, gray)

            # taking average of left and right eye gaze ratio for better accuracy
            gaze_ratio = (gaze_ratio_left_eye + gaze_ratio_right_eye)/2
            # cv2.putText(frame, str(gaze_ratio), (50, 150),
            #             cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

            # determine using gaze ratio which direction is user seeing
            if gaze_ratio <= 0.6:
                cv2.putText(frame, "RIGHT", (50, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                center_count.append(0)
            elif 0.6 < gaze_ratio < 2.0:
                cv2.putText(frame, "CENTER", (50, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                center_count.append(1)
            elif gaze_ratio > 2.0:
                cv2.putText(frame, "LEFT", (50, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            # center_count.append(0)

        cv2.imshow("frame", frame)
        # print(center_count)
        frame = frame.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        key = cv2.waitKey(1)
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


@app.route("/home")
def home():
    return render_template('index.html')


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
