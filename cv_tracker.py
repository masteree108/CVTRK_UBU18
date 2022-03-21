import cv2
import sys
import enum
from random import randint
import log as PYM
from _pydecimal import Decimal, Context, ROUND_HALF_UP
import mot_class as mtc
import yolo_object_detection as yolo_obj
import numpy as np

class IMAGE_DEBUG(enum.Enum):
    # SW_VWB: show video with bbox 
    SW_VWB = 0
    # SE_IWB: save image with bbox 
    SE_IWB  = 1
    # SIWB: save viedo with bbox 
    SE_VWB  = 2
    

class CV_TRACKER():
# private
    # unit: second ,DP=Decimal point
    __frame_timestamp_DP_15fps = [0, 0.066667, 0.133333, 0.2, 0.266667, 0.333333,
                       0.4, 0.466667, 0.533333, 0.6, 0.666667, 0.733333,
                       0.8, 0.866667, 0.933333]

    __format_15fps = ['mp4', '066667', '133333', '2', '266667', '333333',
                       '4', '466667', '533333', '6', '666667', '733333',
                       '8', '866667', '933333']

    # if there is needing another format fps please adding here

    __frame_timestamp_DP_6fps = [0, 0.166667, 0.333333, 0.5, 0.666667, 0.833333]
    __format_6fps = ['mp4', '166667', '333333', '5', '666667', '833333']

    __frame_timestamp_DP_5fps = [0, 0.2, 0.4, 0.6, 0.8]
    __format_5fps = ['mp4', '2', '4', '6', '8']

    '''
        pick up frame description:
        if source_video_fps = 29,
        (1) setted project frame rate = 29, pick up 29 frames(1sec)
            pick_up_frame_interval = 1
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            0               | == 1-1 (pick_up_interval -1)
            1               | == 2-1 
            2               | == 3-1
            ...
            28              | == 29-1

        (2) setted project frame rate = 15, only pick 15 frames from 30 frames(1sec)
            pick_up_frame_interval = round(29/15) = 2
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            1               | == 2-1 (pick_up_interval -1)
            3               | == 4-1 
            5               | == 6-1
            7               | == 8-1
            9               | == 10-1
            11              | == 12-1
            13              | == 14-1
            15              | == 16-1
            17              | == 18-1
            19              | == 20-1
            21              | == 22-1
            23              | == 24-1
            25              | == 26-1
            27              | == 28-1
            29              | == 30-1

        (3) setted project frame rate = 6, only pick 6 frames from 30 frames(1 sec)
            pick_up_frame_interval = round(29/6) = 5
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            4               | == 5-1 (pick_up_interval -1)
            9               | == 10-1 
            14              | == 15-1
            19              | == 20-1
            24              | == 25-1
            29              | == 30-1

        (4) setted project frame rate = 5, only pick 5 frames from 30 frames(1 sec)
            pick_up_frame_interval = round(29/5) = 6
            loop_counter(start number is 0)
            pick up frame:  | judgement:   
            5               | == 6-1 (pick_up_interval -1)
            11              | == 12-1 
            17              | == 18-1
            23              | == 24-1
            29              | == 30-1

    '''


    __video_path = ''
    __video_cap = 0
    __tracker = 0
    __image_debug = [0,0,0]
    __bbox_colors = []
    __vott_video_fps = 0
    __previous_bbox = []
    __calibrated_bboxes = []
    __calibration_IOU = 0.1
    __calibrate_bbox_failed  = False

    def __check_which_frame_number(self, format_value, format_fps):
        for count in range(len(format_fps)):
            if format_value == format_fps[count]:
                return count + 1
    
    def __show_video_with_bounding_box(self, window_name ,frame, wk_value):
        cv2.imshow(window_name, frame)
        cv2.waitKey(wk_value)

    def __check_bbox_shift_over_threshold(self, previous_bbox, current_bbox):
        self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed check, previous_bbox:%s' % previous_bbox)
        self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed check, previous_bbox:%s' % current_bbox)
        X_diff = abs(previous_bbox[0] - current_bbox[0])
        # diff = 0 that equals tracker couldn't trace this bbox
        if X_diff == 0:
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, current_X -previous_X = %.2f' % X_diff)
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, currect_X = bbox[0]: %.2f' % current_bbox[0])
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, previous_X = bbox[0]: %.2f' % previous_bbox[0])
            return True
        Y_diff = abs(previous_bbox[1] - current_bbox[1])
        if Y_diff == 0:
            self.pym.PY_LOG(False, 'W', self.__class__, 'track_failed, current_Y -previous_Y = %.2f'% Y_diff)
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, currect_Y = bbox[1]: %.2f' % current_bbox[1])
            self.pym.PY_LOG(False, 'E', self.__class__, 'track_failed, previous_Y = bbox[1]: %.2f' % previous_bbox[1])
            return True
        return False

    def __IOU_check_for_first_frame(self, user_bboxes, yolo_bboxes):
        self.pym.PY_LOG(False, 'D', self.__class__, '__IOU_check_for_first_frame')
        update_bboxes = []
        for i,user_bbox in enumerate(user_bboxes):
            iou_temp = []
            boxSRCArea = (user_bbox[2] + 1) * (user_bbox[3] + 1)
            for i, yolo_bbox in enumerate(yolo_bboxes):
                xA = max(user_bbox[0], yolo_bbox[0])
                # print("xA:%.2f" % xA)
                yA = max(user_bbox[1], yolo_bbox[1])
                # print("yA:%.2f" % yA)
                xB = min(user_bbox[0] + user_bbox[2], yolo_bbox[0] + yolo_bbox[2])
                # print("xB:%.2f" % xB)
                yB = min(user_bbox[1] + user_bbox[3], yolo_bbox[1] + yolo_bbox[3])
                # print("yB:%.2f" % yB)
                interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
                # print("interArea:%.2f" % interArea)
         
                boxADJArea = (yolo_bbox[2] + 1) * (yolo_bbox[3] + 1)
                # compute the intersection over union by taking the intersection
                # area and dividing it by the sum of prediction  ground-truth
                # areas - the intersection area
                iou = interArea / float(boxSRCArea + boxADJArea - interArea)
                iou_temp.append(iou)
         
            iou_array = np.array(iou_temp)
            index = np.argmax(iou_array)
            self.pym.PY_LOG(False, 'D', self.__class__, "bbox_SRCArea:%d"%boxSRCArea)
            '''
            if boxSRCArea >= 500000:
                calibration_IOU = 0.4
            elif boxSRCArea < 400000 and boxSRCArea >= 300000:
                calibration_IOU = 0.3
            elif boxSRCArea < 300000 and boxSRCArea >= 200000:
                calibration_IOU = 0.2
            elif boxSRCArea < 200000 and boxSRCArea >= 0:
                calibration_IOU = 0.1
            print(iou_array[index])
            if iou_array[index] >= calibration_IOU:
            '''
            if iou_array[index] >= self.__calibration_IOU:
                # this condition that expresses needs use calibrated bbox from yolo
                update_bboxes.append(yolo_bboxes[index])
            else:
                # this condition that expresses no needs use calibrated bbox from yolo
                update_bboxes.append(user_bbox)
        return update_bboxes


    def __run_bbox_calibration(self, frame, user_bboxes, bbox_calibration_strength, debug_img_sw):
        self.__calibrated_bboxes = []
        # 1.using yolov3 to calibarte bbox
        self.pym.PY_LOG(False, 'D', self.__class__, "bbox_calibration_strength:%s"%bbox_calibration_strength)
        yolo_v3 = yolo_obj.yolo_object_detection('person')
        yolo_bboxes = []
        yolo_bboxes = yolo_v3.run_detection(frame, bbox_calibration_strength, False) #last parameter is an switch to save after yolo result image
        #self.pym.PY_LOG(False, 'D', self.__class__, '__run_bbox_calibration:yolo_bboxes')
        #self.pym.PY_LOG(False, 'D', self.__class__, yolo_bboxes)

        if len(yolo_bboxes) != 0:
            calibrated_bboxes = self.__IOU_check_for_first_frame(user_bboxes, yolo_bboxes)
            self.pym.PY_LOG(False, 'D', self.__class__, '__run_bbox_calibration:user_bboxes')
            self.pym.PY_LOG(False, 'D', self.__class__, user_bboxes)

            if debug_img_sw == True:
                compare_frame = frame.copy()
                for i, yolo_bbox in enumerate(yolo_bboxes):                                                                    
                    (x, y) = (yolo_bbox[0], yolo_bbox[1])
                    (w, h) = (yolo_bbox[2], yolo_bbox[3])
                    cv2.rectangle(compare_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                for i, user_bbox in enumerate(user_bboxes):
                    bbox_temp = []
                    bbox_temp.append(int(user_bbox[0]))
                    bbox_temp.append(int(user_bbox[1]))
                    bbox_temp.append(int(user_bbox[2]))
                    bbox_temp.append(int(user_bbox[3]))
                    
                    (x, y) = (bbox_temp[0], bbox_temp[1])
                    (w, h) = (bbox_temp[2], bbox_temp[3])
                    cv2.rectangle(compare_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

                cv2.imwrite("IOU.png", compare_frame)

            # 2. save those bboxes which calibrated
            update_bboxes = []
            for i,bbox in enumerate(calibrated_bboxes):
                bbox_p0 = bbox[0]   #left
                bbox_p1 = bbox[1]   #top
                bbox_p2 = bbox[2]   #width
                bbox_p3 = bbox[3]   #height
                update_bboxes.append((bbox_p0, bbox_p1, bbox_p2, bbox_p3))
                self.__calibrated_bboxes.append([])
                self.__calibrated_bboxes[i].append(bbox_p3) #height
                self.__calibrated_bboxes[i].append(bbox_p2) #width
                self.__calibrated_bboxes[i].append(bbox_p0) #left
                self.__calibrated_bboxes[i].append(bbox_p1) #top

            self.pym.PY_LOG(False, 'D', self.__class__, "__run_bbox_calibration,calibrated_bboxes:")
            self.pym.PY_LOG(False, 'D', self.__class__, update_bboxes)

            self.__calibrate_bbox_failed  = False
            return update_bboxes
        else:
            self.__calibrate_bbox_failed  = True
            return user_bboxes

# public
    def __init__(self, video_path):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True) 
        self.__video_path = video_path 

    #del __del__(self):
        #deconstructor     

    def opencv_setting(self, algorithm, label_object_time_in_video, bboxes, image_debug, \
                    cv_tracker_version, bbox_calibration, bbox_calibration_strength, video_size):
        # 1. make sure video is existed
        self.__video_cap = cv2.VideoCapture(self.__video_path)
        if not self.__video_cap.isOpened():
            self.pym.PY_LOG(False, 'E', self.__class__, 'open video failed!!.')
            return False
        self.__video_size = video_size

        # 2. reading video strat time at the time that user using VoTT to label trakc object
        # *1000 because CAP_PROP_POS_MESE is millisecond
        self.__video_cap.set(cv2.CAP_PROP_POS_MSEC, label_object_time_in_video*1000)                              
        # ex: start time at 50s
        # self.video_cap.set(cv2.CAP_PROP_POS_MSEC, 50000)
        # self.__video_cap.set(cv2.CAP_PROP_FPS, 15)  #set fps to change video,but not working!!

        # 3. setting tracker algorithm and init(one object also can use)
        frame = self.capture_video_frame()
        for bbox in bboxes:
            self.__bbox_colors.append((randint(64, 255), randint(64, 255), randint(64, 255)))

        # 4. using yolov3 to calibrate bbox's height and width or not
        if bbox_calibration == True:
            # avoiding read video size from capture_video_frame  not equl video size by vott setting
            frame_for_calib = cv2.resize(frame, (video_size[0], video_size[1]))
            bboxes = self.__run_bbox_calibration(frame_for_calib, bboxes, bbox_calibration_strength, False)
            
        self.MTC = mtc.mot_class(frame, bboxes, algorithm)

        process_task_num = self.MTC.read_process_task_num()
        
        self.pym.PY_LOG(False, 'D', self.__class__, 'process_task_num:')
        self.pym.PY_LOG(False, 'D', self.__class__, process_task_num)
        self.pym.PY_LOG(False, 'D', self.__class__, 'VoTT_CV_TRACKER initial ok')
       
        # 20201025 ROI function is not maintained
        #if ROI_get_bbox:
          # bbox = self.use_ROI_select('ROI_select', frame)
    
        # 5. for debuging
        self.__image_debug[IMAGE_DEBUG.SW_VWB.value] = image_debug[0]
        self.__image_debug[IMAGE_DEBUG.SE_IWB.value] = image_debug[1]
        self.__image_debug[IMAGE_DEBUG.SE_VWB.value] = image_debug[2]
        if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1 or \
           self.__image_debug[IMAGE_DEBUG.SE_IWB.value] == 1 or \
           self.__image_debug[IMAGE_DEBUG.SE_VWB.value] == 1 :
            self.window_name = "tracking... ( " +  cv_tracker_version + " )"
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)                                                   
            cv2.resizeWindow(self.window_name, 1280, 720)

        # 6. just show video format information
        self.show_video_format_info()

        
        # 7. save init bboxes for checking track failed condition
        for i, bbox in enumerate(bboxes):
            temp = []
            temp.append(bbox[0])
            temp.append(bbox[1])
            temp.append(bbox[2])
            temp.append(bbox[3])
            self.__previous_bbox.append(temp)
        self.pym.PY_LOG(False, 'D', self.__class__, 'self.__previous_bbox:%s'% self.__previous_bbox)

        self.pym.PY_LOG(False, 'D', self.__class__, 'VoTT_CV_TRACKER initial ok')
        return True

    def check_support_fps(self, vott_video_fps):
        self.__vott_video_fps = vott_video_fps
        if vott_video_fps == 15:
            return True
        # for adding new fps format use, please write it here
        elif vott_video_fps == 6:
            return True
        elif vott_video_fps == 5:
            return True
        else:
            self.pym.PY_LOG(False, 'E', self.__class__, 'This version only could track 5 or 15 fps that user setting on the VoTT')
            return False


    def capture_video_frame(self):
        ok, frame = self.__video_cap.read()
        if not ok:
            self.pym.PY_LOG(False, 'E', self.__class__, 'open video failed!!')
            sys.exit()
        #try:                           
        #    frame = cv2.resize(frame, (1280, 720))                                                                         
        #except:      
        #   self.pym.PY_LOG(False, 'E', "frame resize failed!!")
        return frame

    
    def get_label_frame_number(self, format_value):
        # check which frame that user use VoTT tool to label
        fps = self.__vott_video_fps
        if fps == 15:
            return self.__check_which_frame_number(format_value, self.__format_15fps)
        # for adding new fps format use, please write it here
        elif fps == 6:
            return self.__check_which_frame_number(format_value, self.__format_6fps)
        elif fps == 5:
            return self.__check_which_frame_number(format_value, self.__format_5fps)
    
    def get_now_format_value(self, frame_count):
        # check which frame that user use VoTT tool to label
        fps = self.__vott_video_fps
        fc = frame_count -1
        if fps == 15:
            return self.__format_15fps[fc]
        elif fps == 6:
            return self.__format_6fps[fc]
        elif fps == 5:
            return self.__format_5fps[fc]
   
    def use_ROI_select(self, ROI_window_name, frame):
        cv2.namedWindow(ROI_window_name, cv2.WINDOW_NORMAL)                                                   
        cv2.resizeWindow(ROI_window_name, 1280, 720)
        bbox = cv2.selectROI(ROI_window_name, frame, False)
        cv2.destroyWindow(ROI_window_name)
        return bbox

       
    def draw_boundbing_box_and_get(self, frame, ids):
        ok, bboxes = self.MTC.update(frame)
        remove_tuple_bboxes = []
        track_state = {'no_error': True, 'failed_id': 'no_id'}
        if ok:
            # show tracking result
            for i,bbox in enumerate(bboxes):
                remove_tuple_bboxes.append([])
                #print(bbox)
                (startX, startY, endX, endY) = bbox
                remove_tuple_bboxes[i].append(startX)
                remove_tuple_bboxes[i].append(startY)
                remove_tuple_bboxes[i].append(endX)
                remove_tuple_bboxes[i].append(endY)
                p1 = (int(startX), int(startY))
                p2 = (int(endX), int(endY))
                # below rectangle last parameter = return frame picture
                self.pym.PY_LOG(False, 'D', self.__class__, "self.__video_size[0]:%d" % self.__video_size[0])
                self.pym.PY_LOG(False, 'D', self.__class__, "self.__video_size[1]:%d" % self.__video_size[1])
                #frame_for_show = v2.resize(frame, (int(self.__video_size[0]), int(self.__video_size[1])))
                frame = cv2.resize(frame, (self.__video_size[0], self.__video_size[1]))
                cv2.rectangle(frame, p1, p2, self.__bbox_colors[i], 3)
                # add ID onto video
                cv2.putText(frame, ids[i], (p1), cv2.FONT_HERSHEY_SIMPLEX, 2, self.__bbox_colors[i], 3)
        else:
            track_state.update({'no_error': False, 'failed_id':"no_id"})
            for i, newbox in enumerate(bboxes):
                self.pym.PY_LOG(False, 'W', self.__class__, 'track_failed_check id: %s' % ids[i])
                if self.__check_bbox_shift_over_threshold(self.__previous_bbox[i], newbox):
                    track_state.update({'no_error': False, 'failed_id':ids[i]})
                    break
            bboxes = [0,0,0,0]
            if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1 or \
               self.__image_debug[IMAGE_DEBUG.SE_IWB.value] == 1 or \
               self.__image_debug[IMAGE_DEBUG.SE_VWB.value] == 1 :
                cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 3, 255), 2)
                self.pym.PY_LOG(False, 'E', self.__class__, 'Tarcking failre detected')
            else:
                self.pym.PY_LOG(False, 'E', self.__class__, 'Tarcking failre detected')
                

        if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1:
            # showing video with bounding box
            self.__show_video_with_bounding_box(self.window_name ,frame, 1)
         
        self.__previous_bbox = []
        for i, bbox in enumerate(remove_tuple_bboxes):
            self.__previous_bbox.append(bbox)
        return remove_tuple_bboxes, track_state

    def use_waitKey(self, value):
        cv2.waitKey(value)

    def show_video_format_info(self):
        self.pym.PY_LOG(False, 'D', self.__class__, '===== source video format start =====')
        wid = int(self.__video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        hei = int(self.__video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_rate = int(self.__video_cap.get(cv2.CAP_PROP_FPS))
        frame_num = int(self.__video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.pym.PY_LOG(False, 'D', self.__class__, 'video width: %d' % wid)
        self.pym.PY_LOG(False, 'D', self.__class__, 'height: %d' % hei)
        
        # below framenum / framerate = video length
        self.pym.PY_LOG(False, 'D', self.__class__, 'framerate: %.5f' % frame_rate)
        self.pym.PY_LOG(False, 'D', self.__class__, 'framenum: %d' % frame_num)
        video_length = float(frame_num / frame_rate)
        self.pym.PY_LOG(False, 'D', self.__class__, 'video length: %.5f secs' % video_length)
        self.pym.PY_LOG(False, 'D', self.__class__, '===== source video format over =====')
    
    def get_now_frame_timestamp_DP(self, frame_count):
        fc = frame_count -1
        fps = self.__vott_video_fps
        if fps == 15:
            return self.__frame_timestamp_DP_15fps[fc]
        elif fps == 6: 
            return self.__frame_timestamp_DP_6fps[fc]
        elif fps == 5: 
            return self.__frame_timestamp_DP_5fps[fc]
    
    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__class__, msg)

    def set_video_strat_frame(self, time):
        self.__video_cap.set(cv2.CAP_PROP_POS_MSEC, time*1000)                              

    def destroy_debug_window(self):
        cv2.destroyWindow(self.window_name)

    def get_source_video_fps(self):
        return int(self.__video_cap.get(cv2.CAP_PROP_FPS))

    def get_every_second_last_frame_timestamp(self):
        fps = self.__vott_video_fps
        if fps == 15:
            return self.__frame_timestamp_DP_15fps[fps - 1]
        elif fps == 6:
            return self.__frame_timestamp_DP_6fps[fps - 1]   
        elif fps == 5:
            return self.__frame_timestamp_DP_5fps[fps - 1]   

    def get_pick_up_frame_interval(self, vott_video_fps):
        source_video_fps = self.get_source_video_fps()
        self.pym.PY_LOG(False, 'D', self.__class__, 'source_video_fps: %d' % source_video_fps)
                                
        interval = float(source_video_fps / vott_video_fps)
        
        # round 
        interval = Context(prec=1, rounding=ROUND_HALF_UP).create_decimal(interval)
        self.pym.PY_LOG(False, 'D', self.__class__, 'pick up frame interval : %.2f' % interval)                                                                  
        return interval

    def get_update_frame_interval(self, tracking_fps):
        source_video_fps = self.get_source_video_fps()
                                
        interval = float(source_video_fps / tracking_fps)
        
        # round 
        interval = Context(prec=1, rounding=ROUND_HALF_UP).create_decimal(interval)
        self.pym.PY_LOG(False, 'D', self.__class__, 'update frame interval : %.2f' % interval)                                                                  
        return interval

    def get_bbox_calibration(self):
        return self.__calibrated_bboxes, self.__calibrate_bbox_failed

