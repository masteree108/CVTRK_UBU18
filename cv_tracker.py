import cv2
import sys
import enum
from random import randint
import log as PYM
from _pydecimal import Decimal, Context, ROUND_HALF_UP

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
    __frame_timestamp_DP_5fps = [0, 0.2, 0.4, 0.6, 0.8]
    __format_5fps = ['mp4', '2', '4', '6', '8']

    '''
        pick up frame description:
        if source_video_fps = 29,
        (1) setted project frame rate = 15, only pick 15 frames from 30 frames(1sec)
            pick_up_frame_interval = round(29/15) = 2
            loop_counter(start number is 0)
            pick up frame:  | judgemanet:   
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

    (2) setted project frame rate = 5, only pick 5 frames from 30 frames(1 sec)
            pick_up_frame_interval = round(29/5) = 6
            loop_counter(start number is 0)
            pick up frame:  | judgemanet:   
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

    def __get_algorithm_tracker(self, algorithm):
        
        if algorithm == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        elif algorithm == 'MIL':  
            tracker = cv2.TrackerMIL_create()
        elif algorithm == 'KCF':  
            tracker = cv2.TrackerKCF_create()
        elif algorithm == 'TLD':  
            tracker = cv2.TrackerTLD_create()
        elif algorithm == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        elif algorithm == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
        elif algorithm == 'CSRT':                       
            tracker = cv2.TrackerCSRT_create()
        elif algorithm == 'MOSSE':                                                                                          
            tracker = cv2.TrackerMOSSE_create()
        else: 
            #default settings
            tracker = cv2.TrackerCSRT_create()
        return tracker

    def __check_which_frame_number(self, format_value, format_fps):
        for count in range(len(format_fps)):
            if format_value == format_fps[count]:
                return count + 1
    
    def __show_video_with_bounding_box(self, window_name ,frame, wk_value):
        cv2.imshow(window_name, frame)
        cv2.waitKey(wk_value)

# public
    def __init__(self, video_path):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True) 
        self.__video_path = video_path 

    #del __del__(self):
        #deconstructor     

    def opencv_setting(self, algorithm, label_object_time_in_video, bboxes, image_debug):
        # 1. make sure video is existed
        self.__video_cap = cv2.VideoCapture(self.__video_path)
        if not self.__video_cap.isOpened():
            self.pym.PY_LOG(False, 'E', self.__class__, 'open video failed!!.')
            return False

        # 2. reading video strat time at the time that user using VoTT to label trakc object
        # *1000 because CAP_PROP_POS_MESE is millisecond
        self.__video_cap.set(cv2.CAP_PROP_POS_MSEC, label_object_time_in_video*1000)                              
        # ex: start time at 50s
        # self.video_cap.set(cv2.CAP_PROP_POS_MSEC, 50000)
        # self.__video_cap.set(cv2.CAP_PROP_FPS, 15)  #set fps to change video,but not working!!

        # 3. setting tracker algorithm and init(one object also can use)
        frame = self.capture_video_frame()
        self.__tracker = cv2.MultiTracker_create()
        for bbox in bboxes:
            self.__bbox_colors.append((randint(64, 255), randint(64, 255), randint(64, 255)))
            self.__tracker.add(self.__get_algorithm_tracker(algorithm), frame, bbox)

        self.pym.PY_LOG(False, 'D', self.__class__, 'VoTT_CV_TRACKER initial ok')
       
        # 20201025 ROI function is not maintained
        #if ROI_get_bbox:
          # bbox = self.use_ROI_select('ROI_select', frame)
    
        # 4. for debuging
        self.__image_debug[IMAGE_DEBUG.SW_VWB.value] = image_debug[0]
        self.__image_debug[IMAGE_DEBUG.SE_IWB.value] = image_debug[1]
        self.__image_debug[IMAGE_DEBUG.SE_VWB.value] = image_debug[2]
        if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1 or \
           self.__image_debug[IMAGE_DEBUG.SE_IWB.value] == 1 or \
           self.__image_debug[IMAGE_DEBUG.SE_VWB.value] == 1 :
            self.window_name = 'debug'
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)                                                   
            cv2.resizeWindow(self.window_name, 1280, 720)

        # 5. just show video format information
        self.show_video_format_info()
        
        self.pym.PY_LOG(False, 'D', self.__class__, 'VoTT_CV_TRACKER initial ok')
        return True

    def check_support_fps(self, vott_video_fps):
        self.__vott_video_fps = vott_video_fps
        if vott_video_fps == 15:
            return True
        # for adding new fps format use, please write it here
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
        elif fps == 5:
            return self.__check_which_frame_number(format_value, self.__format_5fps)
    
    def get_now_format_value(self, frame_count):
        # check which frame that user use VoTT tool to label
        fps = self.__vott_video_fps
        fc = frame_count -1
        if fps == 15:
            return self.__format_15fps[fc]
        elif fps == 5:
            return self.__format_5fps[fc]
   
    def use_ROI_select(self, ROI_window_name, frame):
        cv2.namedWindow(ROI_window_name, cv2.WINDOW_NORMAL)                                                   
        cv2.resizeWindow(ROI_window_name, 1280, 720)
        bbox = cv2.selectROI(ROI_window_name, frame, False)
        cv2.destroyWindow(ROI_window_name)
        return bbox

       
    def draw_boundbing_box_and_get(self, frame, ids):
        ok, bboxes = self.__tracker.update(frame)
        track_success = True
        if ok:
            for i, newbox in enumerate(bboxes):
                p1 = (int(newbox[0]), int(newbox[1]))
                p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))
                # below rectangle last parament = return frame picture
                cv2.rectangle(frame, p1, p2, self.__bbox_colors[i], 4, 0)
                
                # add ID onto video
                cv2.putText(frame, ids[i], (p1), cv2.FONT_HERSHEY_COMPLEX, 2, self.__bbox_colors[i], 3)
        else:
            track_success = False
            bboxes = [0,0,0,0]
            if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1 or \
               self.__image_debug[IMAGE_DEBUG.SE_IWB.value] == 1 or \
               self.__image_debug[IMAGE_DEBUG.SE_VWB.value] == 1 :
                cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 3, 255), 2)
                self.pym.PY_LOG(False, 'W', self.__class__, 'Tarcking failre detected')
            else:
                self.pym.PY_LOG(False, 'W', self.__class__, 'Tarcking failre detected')
                

        if self.__image_debug[IMAGE_DEBUG.SW_VWB.value] == 1:
            # showing video with bounding box
            self.__show_video_with_bounding_box(self.window_name ,frame, 1)
         
        return bboxes, track_success

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


