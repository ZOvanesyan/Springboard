from ctypes import *
from multiprocessing import Process
import scipy.misc
import math
import random
import cv2
import os
from shutil import copy

def sample(probs):
    s = sum(probs)
    probs = [a/s for a in probs]
    r = random.uniform(0, 1)
    for i in range(len(probs)):
        r = r - probs[i]
        if r <= 0:
            return i
    return len(probs)-1

def c_array(ctype, values):
    arr = (ctype*len(values))()
    arr[:] = values
    return arr

class BOX(Structure):
    _fields_ = [("x", c_float),
                ("y", c_float),
                ("w", c_float),
                ("h", c_float)]

class DETECTION(Structure):
    _fields_ = [("bbox", BOX),
                ("classes", c_int),
                ("prob", POINTER(c_float)),
                ("mask", POINTER(c_float)),
                ("objectness", c_float),
                ("sort_class", c_int)]


class IMAGE(Structure):
    _fields_ = [("w", c_int),
                ("h", c_int),
                ("c", c_int),
                ("data", POINTER(c_float))]

class METADATA(Structure):
    _fields_ = [("classes", c_int),
                ("names", POINTER(c_char_p))]

    

#lib = CDLL("/home/pjreddie/documents/darknet/libdarknet.so", RTLD_GLOBAL)
lib = CDLL(b"/usr/src/app/libdarknet.so", RTLD_GLOBAL)
lib.network_width.argtypes = [c_void_p]
lib.network_width.restype = c_int
lib.network_height.argtypes = [c_void_p]
lib.network_height.restype = c_int

predict = lib.network_predict
predict.argtypes = [c_void_p, POINTER(c_float)]
predict.restype = POINTER(c_float)

set_gpu = lib.cuda_set_device
set_gpu.argtypes = [c_int]

make_image = lib.make_image
make_image.argtypes = [c_int, c_int, c_int]
make_image.restype = IMAGE

get_network_boxes = lib.get_network_boxes
get_network_boxes.argtypes = [c_void_p, c_int, c_int, c_float, c_float, POINTER(c_int), c_int, POINTER(c_int)]
get_network_boxes.restype = POINTER(DETECTION)

make_network_boxes = lib.make_network_boxes
make_network_boxes.argtypes = [c_void_p]
make_network_boxes.restype = POINTER(DETECTION)

free_detections = lib.free_detections
free_detections.argtypes = [POINTER(DETECTION), c_int]

free_ptrs = lib.free_ptrs
free_ptrs.argtypes = [POINTER(c_void_p), c_int]

network_predict = lib.network_predict
network_predict.argtypes = [c_void_p, POINTER(c_float)]

reset_rnn = lib.reset_rnn
reset_rnn.argtypes = [c_void_p]

load_net = lib.load_network
load_net.argtypes = [c_char_p, c_char_p, c_int]
load_net.restype = c_void_p

do_nms_obj = lib.do_nms_obj
do_nms_obj.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

do_nms_sort = lib.do_nms_sort
do_nms_sort.argtypes = [POINTER(DETECTION), c_int, c_int, c_float]

free_image = lib.free_image
free_image.argtypes = [IMAGE]

letterbox_image = lib.letterbox_image
letterbox_image.argtypes = [IMAGE, c_int, c_int]
letterbox_image.restype = IMAGE

load_meta = lib.get_metadata
lib.get_metadata.argtypes = [c_char_p]
lib.get_metadata.restype = METADATA

load_image = lib.load_image_color
load_image.argtypes = [c_char_p, c_int, c_int]
load_image.restype = IMAGE

rgbgr_image = lib.rgbgr_image
rgbgr_image.argtypes = [IMAGE]

predict_image = lib.network_predict_image
predict_image.argtypes = [c_void_p, IMAGE]
predict_image.restype = POINTER(c_float)

def classify(net, meta, im):
    out = predict_image(net, im)
    res = []
    for i in range(meta.classes):
        res.append((meta.names[i], out[i]))
    res = sorted(res, key=lambda x: -x[1])
    return res

def detect(net, meta, image, thresh=.5, hier_thresh=.5, nms=.45):
    im = load_image(image, 0, 0)
    num = c_int(0)
    pnum = pointer(num)
    predict_image(net, im)
    dets = get_network_boxes(net, im.w, im.h, thresh, hier_thresh, None, 0, pnum)
    num = pnum[0]
    if (nms): do_nms_obj(dets, num, meta.classes, nms);
    
    res = []
    for j in range(num):
        for i in range(meta.classes):
            if dets[j].prob[i] > 0:
                b = dets[j].bbox
                res.append((meta.names[i], dets[j].prob[i], (b.x, b.y, b.w, b.h)))
    res = sorted(res, key=lambda x: -x[1])
    free_image(im)
    free_detections(dets, num)
    return res

def process(image_folder, video_name, images, video, net, meta):

    for image in images:
        image="Img/" + image
        
        r = detect(net, meta, image.encode('utf-8'))

        i=0
        
        #load image in cv2
        img = cv2.imread(image,cv2.COLOR_BGR2RGB) 
        box_color=(0,0,0) 

        while i<len(r):
            
            result = str(r[i][0])
             
            if "truck" in result:
                box_color=(0,255,0)
            elif "traffic light" in result:
                box_color=(0,255,255)
            elif "bicycle" in result:    
                box_color=(0,0,255)
            elif "car" in result:    
                box_color=(255,0,0)
            elif "person" in result:
                box_color=(255,165,0)
        
            #bounding box
            c_x = int(r[i][2][0])
            c_y = int(r[i][2][1])
            width = int(r[i][2][2])
            height = int(r[i][2][3])
               
            upper_left_x = int(c_x - width/2) 
            upper_left_y = int(c_y + height/2)
            lower_right_x = int(c_x + width/2)
            lower_right_y = int(c_y - height/2)
               
            #add bounding box to image
            cv2.rectangle(img,(upper_left_x,upper_left_y),(lower_right_x,lower_right_y),box_color,1)
            
            #add label on bounding box
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img,result[1:],(c_x,c_y),font,0.55,box_color,1,cv2.LINE_AA)
            
            i=i+1

        cv2.imwrite(image,img)
        imf=''
        video.write(cv2.imread(os.path.join(imf, image), cv2.COLOR_BGR2RGB))        

    cv2.destroyAllWindows()
    video.release()

    copy(video_name, '/usr/src/app/video/')
    

def FrameCapture(path): 
      
    import os

    # Path to video file 
    vidObj = cv2.VideoCapture(path) 
  
    # Used as counter variable 
    count = 0
  
    # checks whether frames were extracted 
    success = 1
  
    while success: 
  
        # vidObj object calls read 
        # function extract frames 
        success, image = vidObj.read() 
  
        # Saves the frames with frame-count 
        cv2.imwrite("/usr/src/app/Img/frame%d.jpg" % count, image) 
  
        count += 1
   
    count = count - 1
    filename = "frame" + str(count) + ".jpg"
    path = "/usr/src/app/Img/" + filename

    os.remove(path)    
    return 0 

if __name__ == "__main__":

    image_folder = 'Img'
    video_name = 'video.avi'

    FrameCapture('/usr/src/app/video/test.mp4')

    images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
    frame = cv2.imread(os.path.join(image_folder, images[0]), cv2.COLOR_BGR2RGB)
    height, width, layers = frame.shape

    video = cv2.VideoWriter(video_name, 0, 1, (width,height), cv2.COLOR_BGR2RGB)
    
    net = load_net(b"/usr/src/app/cfg/yolov3.cfg", b"/usr/src/app/yolov3.weights", 0)
    meta = load_meta(b"/usr/src/app/cfg/coco.data")
 
    #process(image_folder, video_name, images, video, net, meta)
    p1 = Process(target = process(image_folder, video_name, images, video, net, meta))
    p1.start()
    
 

