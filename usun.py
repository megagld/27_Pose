import cv2

cap = cv2.VideoCapture('test.mp4')
frame_times=[]

frame_no = 0
while(cap.isOpened()):
    frame_exists, curr_frame = cap.read()
    if frame_exists:
        print("for frame : " + str(frame_no) + "   timestamp is: ", str(cap.get(cv2.CAP_PROP_POS_MSEC)))
        frame_times.append(cap.get(cv2.CAP_PROP_POS_MSEC))
    else:
        break
    frame_no += 1

cap.release()

ftp=[]
print(frame_times)
for i,j in zip(frame_times,frame_times[1:]):
    print(1000/(i-j))
    ftp.append(1000/(i-j))

print('x'*10)
print(min(ftp[1:]))
print(max(ftp[1:]))
