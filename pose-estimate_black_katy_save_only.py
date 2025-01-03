import cv2
import torch
import argparse
import numpy as np
from torchvision import transforms
from utils.datasets import letterbox
from utils.torch_utils import select_device
from models.experimental import attempt_load
from general_bm import non_max_suppression_kpt,strip_optimizer
import json
          
@torch.no_grad()
def run(poseweights="yolov7-w6-pose.pt",source="test.mp4",device='cpu',view_img=False,
        save_conf=False,line_thickness = 3,hide_labels=True, hide_conf=True, output_folder="test.mp4"):

    print('File: '+source)

    frame_count = 0  #count no of frames
    kpts_to_store={}
    frames_times=[]

    device = select_device(opt.device) #select device

    model = attempt_load(poseweights, map_location=device)  #Load model
    _ = model.eval()
   
    if source.isnumeric() :    
        cap = cv2.VideoCapture(int(source))    #pass video to videocapture object
    else :
        cap = cv2.VideoCapture(source)    #pass video to videocapture object
   
    if (cap.isOpened() == False):   #check if videocapture not opened
        print('Error while trying to read video. Please check path again')
        raise SystemExit()

    else:
        frame_width = int(cap.get(3))  #get video frame width
       
        source_video_name = f"{source.split('\\')[-1]}"
        
        while(cap.isOpened): #loop until cap opened or video not complete
        
            print("Frame {} Processing".format(frame_count))

            ret, frame = cap.read()  #get frame and success from video capture
            
            if ret: #if success is true, means frame exist
                frame_time=cap.get(cv2.CAP_PROP_POS_MSEC) #frame timpestamp
                frames_times.append(frame_time)

                orig_image = frame #store frame
                image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB) #convert frame to RGB
                image = letterbox(image, (frame_width), stride=64, auto=True)[0]
                image = transforms.ToTensor()(image)
                image = torch.tensor(np.array([image.numpy()]))
            
                image = image.to(device)  #convert image data to device
                image = image.float() #convert image to float precision (cpu)

                with torch.no_grad():  #get predictions
                    output_data, _ = model(image)

                output_data = non_max_suppression_kpt(output_data,   #Apply non max suppression
                                            0.70,   # Conf. Threshold.
                                            0.65, # IoU Threshold.
                                            nc=model.yaml['nc'], # Number of classes.
                                            nkpt=model.yaml['nkpt'], # Number of keypoints.
                                            kpt_label=True)
                
                if output_data:  #check if no pose
                    kpts_to_store[frame_time]=[]
                    pose=output_data[0]
                    for c in pose[:, 5].unique(): # Print results
                        n = (pose[:, 5] == c).sum()  # detections per class
                        print("No of Objects in Current Frame : {}".format(n))

                    for det_index, _ in enumerate(reversed(pose[:,:6])): #loop over poses for drawing on frame

                        kpts = pose[det_index, 6:]

                        kpts_to_store[frame_time]=kpts.tolist()

            else:
                break
            
            frame_count += 1

        # saving kpts to json file

        json_file_name= "{}\\{}".format(output_folder,source_video_name.replace('.mp4','_kpts.json'))

        with open(json_file_name, "w") as jsonfile:
            json.dump(kpts_to_store, jsonfile)

        cap.release()

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--poseweights', nargs='+', type=str, default='yolov7-w6-pose.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default="test.mp4", help='video/0 for webcam') #video source
    parser.add_argument('--device', type=str, default='cpu', help='cpu/0,1,2,3(gpu)')   #device arugments
    parser.add_argument('--view-img', action='store_true', help='display results')  #display results
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels') #save confidence in txt writing
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)') #box linethickness
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels') #box hidelabel
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences') #boxhideconf
    parser.add_argument('--output_folder', type=str, default="test.mp4",) #video output folder
    opt = parser.parse_args()
    return opt
   
#main function
def main(opt):
    run(**vars(opt))

if __name__ == "__main__":
    opt = parse_opt()
    strip_optimizer(opt.device,opt.poseweights)
    main(opt)
