import numpy as np
import cv2
import dlib

cap = cv2.VideoCapture(-1)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("../shape_predictor_68_face_landmarks.dat")


def midpoint(p1, p2):
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)


def get_gaze_ratio(eye_points, facial_landmarks):

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

    cv2.imshow("gray eye", gray_eye)
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
        return 1


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
            [36, 37, 38, 39, 40, 41], landmarks)
        gaze_ratio_right_eye = get_gaze_ratio(
            [42, 43, 44, 45, 46, 47], landmarks)

        # taking average of left and right eye gaze ratio for better accuracy
        gaze_ratio = (gaze_ratio_left_eye + gaze_ratio_right_eye)/2
        # cv2.putText(frame, str(gaze_ratio), (50, 150),
        #             cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

        # determine using gaze ratio which direction is user seeing
        if gaze_ratio <= 0.9:
            cv2.putText(frame, "RIGHT", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        elif 0.9 < gaze_ratio < 1.0:
            cv2.putText(frame, "CENTER", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        elif gaze_ratio > 1.0:
            cv2.putText(frame, "LEFT", (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
    cv2.imshow("frame", frame)
    key = cv2.waitKey(1)
    if key == 27:
        break
cap.release()
cv2.destroyAllWindows()
