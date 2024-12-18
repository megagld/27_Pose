def detect_wheel(canva_1,canva_2,image):

    import numpy
    import cv2
    from ultralytics import YOLO

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hist = cv2.equalizeHist(gray)

    blur = cv2.GaussianBlur(hist, (31,31), cv2.BORDER_DEFAULT)
    height, width = blur.shape[:2]

    size=1

    minR = round(size*width/85)
    maxR = round(size*width/25)
    minDis = round(size*width/17)

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

            # określenie granic w jakich może być koło
            cls = int(box.cls[0])
            # print(cls)
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
            
            #jeśli wykryta jest osoba lub ptak:

            if cls in [0,14]:
                metr=x2-x1

                x2_t=int(x2+metr/2)
                x1_t=int(x1-metr/2)

                y2_t=int(y2+metr/2)
                y1_t=int(y2-metr/1)
                               
            #jeśli wykryty jest rower lub inne:

            else:
                metr=(x2-x1)/2

                x2_t=int(x2)
                x1_t=int(x1)

                y2_t=int(y2)
                y1_t=int(y1)

            x2_t_list.append(x2_t)
            x1_t_list.append(x1_t)
            y2_t_list.append(y2_t)
            y1_t_list.append(y1_t)

    x2_max=max(x2_t_list)    
    x1_min=min(x1_t_list)
    y2_max=max(y2_t_list)    
    y1_min=min(y1_t_list)

    # wyszukiwanie kół tylko na wycinku klatki:

    delay=int(metr)
    crop_img = blur[y1_t-delay:y2_t+delay, x1_t-delay:x2_t+delay]


    circles = cv2.HoughCircles(crop_img, cv2.HOUGH_GRADIENT, 1, minDis, param1=14, param2=25, minRadius=minR, maxRadius=maxR)

    if circles is not None:
        circles = numpy.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:

            x+=x1_t-delay
            y+=y1_t-delay

            if x1_min<x<x2_max and y1_min<y<y2_max:
                c_col=(0, 255, 0)
                cv2.circle(canva_1, (x, y), r, c_col, 2)
                cv2.circle(canva_2, (x, y), r, c_col, 2)

