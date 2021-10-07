import numpy as np;
import cv2

# This script reads numpy files and overlays the corresponding images on the RealSense and ZED camera video feeds.

cap = cv2.VideoCapture(0) #RS camera

#Images are stored as .npy
num = 112538

img = np.load('/home/p4bhattachan/gripper/3DCameraServer/testImages/npyFiles/00softscrub/{}_RS_color.npy'.format(num))
n = 0 # n stores the number of times in which image is zoomed

transparency = 0.6

img_name = "{}_RS_blend.png".format(num)

while cap.isOpened():

    ret, frame = cap.read()

    k = cv2.waitKey(1)

    if k%256 == 43:
        # + pressed to zoom in
        n = n + 1
        img = cv2.resize(img, (100+img.shape[1], 100+img.shape[0]))

    if k%256 == 45:
        # - pressed to zoom out
        if n > 0:
            cv2.destroyWindow("RS {}".format(n))
            n = n - 1
            img = cv2.resize(img, (img.shape[1]-100, img.shape[0]-100))

    if n > 0:
        frame = cv2.resize(frame, (img.shape[1], img.shape[0]))

    if k%256 == 62:
	    # > pressed
	    transparency = transparency + 0.1
    if k%256 == 60:
        # < pressed
        transparency = transparency - 0.1

    blend = cv2.addWeighted(img, transparency, frame, 0.7, 0)

    cv2.imshow("RS {}".format(n), blend)

    if k%256 == 32:
        # SPACE pressed
        cv2.imwrite(img_name, blend) #image of object is captured

    if k%256 == 27:
        # ESC pressed
        break

cap.release()
cv2.destroyAllWindows()
