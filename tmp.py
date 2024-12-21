import cv2

source="D:\\Python\\27_Pose\\_data\\test.mp4"

cap = cv2.VideoCapture(source)    #pass video to videocapture object

ret, frame = cap.read()

cap.set(1,20)
res, img = cap.read()

cv2.imshow("input", img)

cv2.waitKey(0)

print('z')