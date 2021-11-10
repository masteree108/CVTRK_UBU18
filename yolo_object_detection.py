# please goto below link to download yolov4.cfg and yolov4.weights,
# goto this https://github.com/AlexeyAB/darknet/tree/master/cfg/yolov4.cfg and copy those content and save to yolov4.cfg
# wget https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v3_optimal/yolov4.weights
# and put those files into yolo-coco_v4
# import the necessary packages
from imutils.video import FPS
import numpy as np
import argparse
import cv2
import os


class yolo_object_detection():
# private
    __labelsPath = "./yolo-coco_v4/coco.names"
    __weightsPath = "./yolo-coco_v4/yolov4.weights"
    __configPath = "./yolo-coco_v4/yolov4.cfg"
    __confidence_setting = 0.5
    __threshold = 0.2

    def __judge_object_confidence_label_to_get_bbox(self, layerOutputs, boxes, crop_width, crop_height, \
                                                crop_x, crop_y, classIDs):
        #confidences = []
        for output in layerOutputs:
            # loop over each of the detections
            for detection in output:
                # extract the class ID and confidence (i.e., probability)
                # of the current object detection
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]
                if self.__LABELS[classID] !=  self.__target_label:
                    continue

               # filter out weak predictions by ensuring the detected
                # probability is greater than the minimum probability
                if confidence > self.__confidence_setting:
                    # scale the bounding box coordinates back relative to
                    # the size of the image, keeping in mind that YOLO
                    # actually returns the center (x, y)-coordinates of
                    # the bounding box followed by the boxes' width and
                    # height
                    box = detection[0:4] * np.array([crop_width, crop_height, crop_width, crop_height])
                    (centerX, centerY, width, height) = box.astype("int")
                    if width < crop_width / 3:
                        # use the center (x, y)-coordinates to derive the top
                        # and and left corner of the bounding box
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))

                        # update our list of bounding box coordinates,
                        # confidences, and class IDs
                        boxes.append([crop_x + x, crop_y + y, int(width), int(height)])
                        #confidences.append(float(confidence))
                        classIDs.append(classID)

# public
    def __init__(self, target_label):
        np.random.seed(42)
        self.__LABELS = open(self.__labelsPath).read().strip().split("\n")
        self.__COLORS = np.random.randint(0, 255, size=(len(self.__LABELS), 3), dtype="uint8")
        self.__target_label = target_label

    def run_detection(self, frame ,bbox_calibration_strength, output_image_sw):
        # determine only the *output* layer names that we need from YOLO
        self.__net = cv2.dnn.readNetFromDarknet(self.__configPath, self.__weightsPath)
        # determine only the *output* layer names that we need from YOLO
        ln = self.__net.getLayerNames()
        ln = [ln[i[0] - 1] for i in self.__net.getUnconnectedOutLayers()]

        # initialize the width and height of the frames in the video file
        W = None
        H = None

        # if the frame dimensions are empty, grab them
        if W is None or H is None:
            (H, W) = frame.shape[:2]
        # initialize our lists of detected bounding boxes, confidences,
        # and class IDs, respectively
        boxes = []
        #confidences = []
        classIDs = []
        # construct a blob from the input frame and then perform a forward
        # pass of the YOLO object detector, giving us our bounding boxes
        # and associated probabilities
        # crop small area to improve the effect of yolo
        # crop image size 1280*1920
        # overlap 50%
        if bbox_calibration_strength == '0':
            self.__confidence_setting = 0.5
            print("           yolo level0              ")
            # for full image
            pass
        elif bbox_calibration_strength == '1':
            print("           yolo level1              ")
            self.__confidence_setting = 0.6
            crop_width = 1920
            crop_height = 1080
            for crop_x in range(0, 2840, 960):
                for crop_y in range(0, 1620, 540):
                    # print("crop_y:%d" % crop_y)
                    # print("crop_y + crop_height:%d" % (crop_y + crop_height))
                    # print("crop_x:%d" % crop_x)
                    # print("crop_x + crop_width:%d" % (crop_x + crop_width))

                    crop_img = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
                    blob = cv2.dnn.blobFromImage(crop_img, 1 / 255.0, (416, 416),
                                                 swapRB=True, crop=False)
                    self.__net.setInput(blob)
                    layerOutputs = self.__net.forward(ln)
                    # loop over each of the layer outputs
                    self.__judge_object_confidence_label_to_get_bbox(layerOutputs, boxes, crop_width, crop_height, crop_x, crop_y, classIDs)
                
        elif bbox_calibration_strength == '2':
            print("           yolo level2              ")
            self.__confidence_setting = 0.7
            crop_width = 960
            crop_height = 540
            for crop_x in range(0, 3456, 576):
                for crop_y in range(0, 1944, 324):
                    # print("crop_y:%d" % crop_y)
                    # print("crop_y + crop_height:%d" % (crop_y + crop_height))
                    # print("crop_x:%d" % crop_x)
                    # print("crop_x + crop_width:%d" % (crop_x + crop_width))

                    crop_img = frame[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
                    blob = cv2.dnn.blobFromImage(crop_img, 1 / 255.0, (416, 416),
                                                 swapRB=True, crop=False)
                    self.__net.setInput(blob)
                    layerOutputs = self.__net.forward(ln)
                    # loop over each of the layer outputs
                    self.__judge_object_confidence_label_to_get_bbox(layerOutputs, boxes, crop_width, crop_height, crop_x, crop_y, classIDs)

        # full image
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
                                     swapRB=True, crop=False)
        self.__net.setInput(blob)
        layerOutputs = self.__net.forward(ln)
        self.__judge_object_confidence_label_to_get_bbox(layerOutputs, boxes, W, H, 0, 0, classIDs)
        if output_image_sw == True:
            out_frame = frame.copy()
            for i, bbox in enumerate(boxes):
                (x, y) = (bbox[0], bbox[1])
                (w, h) = (bbox[2], bbox[3])
                color = [int(c) for c in self.__COLORS[classIDs[i]]]
                cv2.rectangle(out_frame, (x, y), (x + w, y + h), color, 2)

            cv2.imwrite("yolov4_detection_without_nms.png", out_frame)
        # apply non-maxima suppression to suppress weak, overlapping
        # bounding boxes
        '''
        # no use NMS
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, self.__confidence_setting, self.__threshold)

        # ensure at least one detection exists
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                # extract the bounding box coordinates
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])
                #x = x + int(w/5)
                # draw a bounding box rectangle and label on the frame
                if self.__LABELS[classIDs[i]] == self.__target_label:
                    color = [int(c) for c in self.__COLORS[classIDs[i]]]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    text = "{}: {:.4f}".format(self.__LABELS[classIDs[i]], confidences[i])
                    cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.imwrite("yolov4_detection_with_nms.png",frame)
        '''
        return boxes

