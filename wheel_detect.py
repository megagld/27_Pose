import numpy
import cv2
from ultralytics import YOLO


image = cv2.imread(".\\data\\nn_dif.jpg")
output = image.copy()

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

hist = cv2.equalizeHist(gray)

blur = cv2.GaussianBlur(hist, (31,31), cv2.BORDER_DEFAULT)
height, width = blur.shape[:2]

# size=.0386995
size=1

minR = round(size*width/85)
maxR = round(size*width/25)
minDis = round(size*width/17)

# minR = round(width/65)
# maxR = round(width/11)
# minDis = round(width/7)

circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, minDis, param1=14, param2=25, minRadius=minR, maxRadius=maxR)

model = YOLO("yolo-Weights/yolov8n.pt")
results = model(image, stream=True)

x2_t_list=[]
x1_t_list=[]
y2_t_list=[]
y1_t_list=[]

# coordinates
for r in results:
    boxes = r.boxes

    for box in boxes:
        # bounding box
        x1, y1, x2, y2 = box.xyxy[0]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

        # # put box in cam
        # cv2.rectangle(output, (x1, y1), (x2, y2), (255, 0, 255), 3)

        # określenie granic w jakich może być koło
        cls = int(box.cls[0])
        #jeśli wykryta jest osoba:
        print(cls)
        classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
                    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
                    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
                    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
                    "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
                    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
                    "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
                    "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
                    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                    "teddy bear", "hair drier", "toothbrush"
                    ]
        if cls==0:
            metr=x2-x1

            x2_t=int(x2+metr/2)
            x1_t=int(x1-metr/2)

            y2_t=int(y2+metr/2)
            y1_t=int(y2-metr/1)
            
            cv2.rectangle(output, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.rectangle(output, (x1_t, y1_t), (x2_t, y2_t), (255, 0, 255), 3)

        #jeśli wykryty jest rower:

        else:
            metr=(x2-x1)/2

            x2_t=int(x2)
            x1_t=int(x1)

            y2_t=int(y2)
            y1_t=int(y1)

            cv2.rectangle(output, (x1, y1), (x2, y2), (155, 0, 255), 3)
            cv2.rectangle(output, (x1_t, y1_t), (x2_t, y2_t), (155, 0, 255), 3)
            cv2.line(output, (x2_t, y1_t), (x1_t, y2_t), (155, 0, 255), 3)

        x2_t_list.append(x2_t)
        x1_t_list.append(x1_t)
        y2_t_list.append(y2_t)
        y1_t_list.append(y1_t)


        # object details
        org = [x1, y1]
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255, 0, 0)
        thickness = 2

        cv2.putText(output, classNames[cls], org, font, fontScale, color, thickness)

# print(minR)
# print(maxR)
# print(minDis)
# print('x'*10)



x2_max=max(x2_t_list)    
x1_min=min(x1_t_list)
y2_max=max(y2_t_list)    
y1_min=min(y1_t_list)

if circles is not None:
    circles = numpy.round(circles[0, :]).astype("int")
    for (x, y, r) in circles:

        if x1_min<x<x2_max and y1_min<y<y2_max:
        # if x1:
            c_col=(0, 255, 0)
        else:
            c_col=(155, 0, 155)

        print(r)
        print('x'*10)
        cv2.circle(output, (x, y), r, c_col, 2)
        rec_size=2
        cv2.rectangle(output, (x - rec_size, y - rec_size), (x + rec_size, y + rec_size), (0, 128, 255), -1)
        cv2.putText(output, str(r), (x - 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

# cv2.imshow("result", numpy.hstack([image, output]))
cv2.imshow("result", output)

cv2.waitKey()