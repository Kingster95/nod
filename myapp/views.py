from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import threading
import numpy
import time

camera = cv2.VideoCapture(0)  # use 0 for web camera
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")


def gen_frames():
    started = False
    start_x = 0
    start_y = 0
    x_dist = 0
    y_dist = 0
    nod = "none"
    max_x = 0
    min_x = 1920
    max_y = 0
    min_y = 1920

    no = 0
    yes = 0
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            faces = face_cascade.detectMultiScale(frame, 1.2, 6)
            for x, y, w, h in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                # cv2.putText(img, 'Face | Nod: none', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
                if started == False:
                    start_time = time.time()
                    started = True
                    start_x = x
                    start_y = y
                    # print("started")
                elif started == True:
                    reset = False
                    elapsed = time.time() - start_time
                    if elapsed <= 4:
                        if x <= min_x:
                            min_x = x
                        if x >= max_x:
                            max_x = x
                        if y >= max_y:
                            max_y = y
                        if y <= min_y:
                            min_y = y
                        # Calculating the left and right distances for "No" nod
                        min_dif = start_x - min_x
                        max_dif = max_x - start_x
                        # Checking which direction involved more movement for "No" nod
                        x_dist = max(min_dif, max_dif)
                        # Calculating the up and down distances for "Yes" nod
                        min_dif_y = start_y - min_y
                        max_dif_y = max_y - start_y
                        # Checking which direction involved more movement for "Yes" nod
                        y_dist = max(min_dif_y, max_dif_y)
                        # print("X Distance: " , x_dist , "Y Distance: " , y_dist)
                    if (
                        x_dist >= 13
                        and abs(start_x - x) <= 4
                        and elapsed < 4
                        and reset == False
                        and x_dist > y_dist
                    ):
                        print("No")
                        no = no + 1
                        reset = True		
                        nod = "No at " + str(time.localtime(time.time()).tm_sec)

                    if (
                        y_dist >= 13
                        and abs(start_y - y) <= 4
                        and elapsed < 4
                        and reset == False
                        and y_dist > x_dist
                    ):
                        print("Yes")
                        yes = yes + 1
                        reset = True
                        nod = "Yes at " + str(time.localtime(time.time()).tm_sec)
                    if elapsed > 4 and started == True:
                        reset = True
                    if reset == True:
                        # print("Reset")
                        start_x = 0
                        start_y = 0
                        x_dist = 0
                        y_dist = 0
                        max_x = 0
                        min_x = 1920
                        max_y = 0
                        min_y = 1920
                        started = False
                        reset = False
                        start_time = 0
                        elapsed = 0
                cv2.putText(
                    frame,
                    "Face || " + nod,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (36, 255, 12),
                    2,
                )
            # cv2.rectangle(frame, (150, 150), (150+150, 150+150), (255, 0, 0), 2)

            ret, buffer = cv2.imencode(".jpg", frame)
            # print(faces)
            frame = buffer.tobytes()
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )  # concat frame one by one and show result


def video_feed(request):
    # Video streaming route. Put this in the src attribute of an img tag
    return StreamingHttpResponse(
        gen_frames(), content_type="multipart/x-mixed-replace; boundary=frame"
    )
