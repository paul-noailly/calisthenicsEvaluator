import cv2 as cv
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
from scipy.ndimage import rotate
from math import acos





def rotate_nn(data, angle, axes):
    """
    Rotate a `data` based on rotating coordinates.
    """

    # Create grid of indices
    shape = data.shape
    d1, d2, d3 = np.mgrid[0:shape[0], 0:shape[1], 0:shape[2]]

    # Rotate the indices
    d1r = rotate(d1, angle=angle, axes=axes)
    d2r = rotate(d2, angle=angle, axes=axes)
    d3r = rotate(d3, angle=angle, axes=axes)

    # Round to integer indices
    d1r = np.round(d1r)
    d2r = np.round(d2r)
    d3r = np.round(d3r)

    d1r = np.clip(d1r, 0, shape[0])
    d2r = np.clip(d2r, 0, shape[1])
    d3r = np.clip(d3r, 0, shape[2])

    return data[d1r, d2r, d3r]





def poseDetector_v2(frame, thr = 0.2):
    BODY_PARTS = { "Nose": 0, "Neck": 1, "RShoulder": 2, "RElbow": 3, "RWrist": 4,
                   "LShoulder": 5, "LElbow": 6, "LWrist": 7, "RHip": 8, "RKnee": 9,
                   "RAnkle": 10, "LHip": 11, "LKnee": 12, "LAnkle": 13, "REye": 14,
                   "LEye": 15, "REar": 16, "LEar": 17, "Background": 18 }

    POSE_PAIRS = [ ["Neck", "RShoulder"], ["Neck", "LShoulder"], ["RShoulder", "RElbow"],
                   ["RElbow", "RWrist"], ["LShoulder", "LElbow"], ["LElbow", "LWrist"],
                   ["Neck", "RHip"], ["RHip", "RKnee"], ["RKnee", "RAnkle"], ["Neck", "LHip"],
                   ["LHip", "LKnee"], ["LKnee", "LAnkle"], ["Neck", "Nose"], ["Nose", "REye"],
                   ["REye", "REar"], ["Nose", "LEye"], ["LEye", "LEar"] ]

    width = 368
    height = 368
    inWidth = width
    inHeight = height

    net = cv.dnn.readNetFromTensorflow("models/graph_opt.pb")


    frameWidth = frame.shape[1]
    frameHeight = frame.shape[0]
    
    net.setInput(cv.dnn.blobFromImage(frame, 1.0, (inWidth, inHeight), (127.5, 127.5, 127.5), swapRB=True, crop=False))
    out = net.forward()
    out = out[:, :19, :, :]  # MobileNet output [1, 57, -1, -1], we only need the first 19 elements

    assert(len(BODY_PARTS) == out.shape[1])

    points = []
    for i in range(len(BODY_PARTS)):
        # Slice heatmap of corresponging body's part.
        heatMap = out[0, i, :, :]

        _, conf, _, point = cv.minMaxLoc(heatMap)
        x = (frameWidth * point[0]) / out.shape[3]
        y = (frameHeight * point[1]) / out.shape[2]
        points.append((int(x), int(y)) if conf > thr else None)
        
    dic_parts = {}
    for pair in POSE_PAIRS:
        partFrom = pair[0]
        partTo = pair[1]
        assert(partFrom in BODY_PARTS)
        assert(partTo in BODY_PARTS)

        idFrom = BODY_PARTS[partFrom]
        idTo = BODY_PARTS[partTo]

        if points[idFrom] and points[idTo]:
            dic_parts[partFrom] = points[idFrom]
            dic_parts[partTo] = points[idTo]
            cv.line(frame, points[idFrom], points[idTo], (0, 255, 0), 3)
            cv.ellipse(frame, points[idFrom], (3, 3), 0, 0, 360, (0, 0, 255), cv.FILLED)
            cv.ellipse(frame, points[idTo], (3, 3), 0, 0, 360, (0, 0, 255), cv.FILLED)

    t, _ = net.getPerfProfile()

    return frame, dic_parts

def get_bodyPart_dict(img_path, plot=False):

    # 1st roation
    input1 = np.rot90(cv.imread(img_path), k=3, axes=(0, 1))
    plt.imshow(input1)
    plt.axis('off')
    plt.savefig(img_path.replace('.jpg','_1_rotated.png'))

    # 2nd rotaion
    input1 = np.rot90(cv.imread(img_path), k=1, axes=(0, 1))
    plt.imshow(input1)
    plt.axis('off')
    plt.savefig(img_path.replace('.jpg','_2_rotated.png'))

    # original image
    plt.imshow(cv.imread(img_path))
    plt.axis('off')

    dic_res = {'0':{}, '1':{}}

    
    # rotation 1
    input = cv.imread(img_path.replace('.jpg','_1_rotated.png'))
    output, dic_parts = poseDetector_v2(input)    
    output1 = rotate_nn(output,90,(0,1))
    x_max = output1.shape[1]
    y_max = output1.shape[0]
    for body_part in dic_parts.keys():
        dic_res['0'][body_part] = (dic_parts[body_part][1],dic_parts[body_part][0])
    
    # rotation 2
    input = cv.imread(img_path.replace('.jpg','_2_rotated.png'))
    output, dic_parts = poseDetector_v2(input)    
    output1 = rotate_nn(output,-90,(0,1))
    x_max = output1.shape[1]
    y_max = output1.shape[0]
    fig, ax = plt.subplots()
    for body_part in dic_parts.keys():
        dic_res['1'][body_part] = (x_max-dic_parts[body_part][1],y_max-dic_parts[body_part][0])




    # removing tmp rotated pictures
    os.remove(img_path.replace('.jpg','_2_rotated.png'))
    os.remove(img_path.replace('.jpg','_1_rotated.png'))

    return dic_res

def get_pos_head(dic_bp, part='head'):
    # for each rotation, create centers of gravity around key areas of the body
    group_head = {"Nose":1,"Neck":1,"REye":1,"LEye":1,"REar":1,"LEar":1, "RShoulder":2, "LShoulder":2}
    group_arms = {"RElbow":1,"RWrist":2,"LElbow":1,"LWrist":2}
    group_legs = {"RKnee":1,"RAnkle":1,"LKnee":1,"LAnkle":1}
    group_hips = {"RHip":1, "LHip":1}
    sub_group_dict = {'head':group_head, 'arms':group_arms, 'legs':group_legs, 'hips':group_hips}[part]
    total_weight = 0
    list_x = []
    list_y = []
    for key in dic_bp:
        if key in sub_group_dict:
            list_x.append(dic_bp[key][0]*sub_group_dict[key])
            list_y.append(dic_bp[key][1]*sub_group_dict[key])
            total_weight += sub_group_dict[key]
    list_x = np.array(list_x)
    list_y = np.array(list_y) 
    if len(list_x) >0 : # we have at list one of the head element inside
        center_gravity = (list_x.sum()/total_weight, list_y.sum()/total_weight)
        std_x = list_x.std()
        std_y = list_y.std()
        return True, center_gravity, std_x, std_y, total_weight
    else:
        return False, None, None, None, total_weight
    
def get_alignement(x,y):
    # alignement metrics, give 1 if head/hips/legs are perfecty aligned
    distance_head_legs = ((x[2]-x[0])**2 + (y[2]-y[0])**2)**0.5
    distance_head_hips = ((x[1]-x[0])**2 + (y[1]-y[0])**2)**0.5
    rad_legs = acos(abs(x[2]-x[0])/distance_head_legs)
    rad_hips = acos(abs(x[1]-x[0])/distance_head_hips)
    degree_legs = rad_legs * 180 / 3.1415
    degree_hips = rad_hips * 180 / 3.1415
    return (45 - abs(degree_legs - degree_hips)) / 45

def get_parallelisme(center_gravity_head, center_gravity_legs):
    # parallelism metric, give 1 if body line if // to the ground
    x1, y1 = center_gravity_head[0], center_gravity_head[1]
    x2, y2 = center_gravity_legs[0], center_gravity_legs[1]
    distance_default = abs(x2-x1)
    distance_body = ((x2-x1)**2 + (y2-y1)**2)**0.5
    rad = acos(distance_default/distance_body)
    degree = rad * 180 / 3.1415
    score = (90 - abs(degree))/90
    return score
    
def get_result_sub_dict(center_gravity_head, center_gravity_arms, center_gravity_legs, center_gravity_hips):
    # create the dic metric dict from centers of gravity. contain name and quality metrics
    quality_metrics = {}
    mvt_name = ''
    # get Name
    if center_gravity_arms != None and center_gravity_head != None:
        if center_gravity_arms[1] > center_gravity_head[1]: #arms are above head => front lever
            mvt_name = 'frontlever'
        else:  #arms are below head => full plnche
            mvt_name = 'fullplanche'
        quality_metrics['name'] = mvt_name 
        quality_metrics['metrics'] = {}
    else:
        return None
    # get quality
    if center_gravity_head != None and center_gravity_legs != None:
        if center_gravity_hips != None: # we have data for hips
            alignement = get_alignement([center_gravity_head[0],center_gravity_hips[0],center_gravity_legs[0]],[center_gravity_head[1],center_gravity_hips[1],center_gravity_legs[1]])
            quality_metrics['metrics']['alignement'] = alignement
        if center_gravity_legs != None: # we have data for legs
            parallelisme = get_parallelisme(center_gravity_head, center_gravity_legs)
            quality_metrics['metrics']['parallelisme'] = parallelisme
        return quality_metrics
    else:
        return None



def choose(dic_res):
    # choose the best rotaion, that is the one with necessary center of gravity to calculate at least 1 metric, and highest number of points
    maxi = -1
    key_to_chose = '0'
    for key in dic_res:        
        is_usable_head, center_gravity_head, std_x_head, std_y_head, total_weight_head = get_pos_head(dic_res[key], 'head')
        is_usable_arms, center_gravity_arms, std_x_arms, std_y_arms, total_weight_arms = get_pos_head(dic_res[key], 'arms')
        is_usable_legs, center_gravity_legs, std_x_legs, std_y_legs, total_weight_legs = get_pos_head(dic_res[key], 'legs')
        is_usable_hips, center_gravity_hips, std_x_hips, std_y_hips, total_weight_hips = get_pos_head(dic_res[key], 'hips')
        if is_usable_head and is_usable_arms and is_usable_legs or is_usable_head and is_usable_arms and is_usable_hips:
            if total_weight_head + total_weight_arms + total_weight_legs + total_weight_hips > maxi:
                maxi = total_weight_head + total_weight_arms + total_weight_legs + total_weight_hips
                key_to_chose = key
    return key_to_chose
        
    

def get_result_dual_dict(dic_res):
    # pick a rotation, then get the metric dic
    key_to_chose = choose(dic_res)
    if key_to_chose != None:
        is_usable_head, center_gravity_head, std_x_head, std_y_head, total_weight_head = get_pos_head(dic_res[key_to_chose], 'head')
        is_usable_arms, center_gravity_arms, std_x_arms, std_y_arms, total_weight_arms = get_pos_head(dic_res[key_to_chose], 'arms')
        is_usable_legs, center_gravity_legs, std_x_legs, std_y_legs, total_weight_legs = get_pos_head(dic_res[key_to_chose], 'legs')
        is_usable_hips, center_gravity_hips, std_x_hips, std_y_hips, total_weight_hips = get_pos_head(dic_res[key_to_chose], 'hips')    
        return get_result_sub_dict(center_gravity_head, center_gravity_arms, center_gravity_legs, center_gravity_hips)
    else:
        return None

def decode(img_path):
    # decode image for dl model, then extrat body part coordinates, and get metrics (or None if body points are insuficient)
    dic_res = get_bodyPart_dict(img_path) # import image, run model, and get dictionnary of bp positions    
    return get_result_dual_dict(dic_res)