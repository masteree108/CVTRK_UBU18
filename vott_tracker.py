import os
import sys
import read_vott_id_json as RVIJ
import write_vott_id_json as WVIJ
import cv_tracker as CVTR 
import log as PYM
import threading 
from tkinter import messagebox

ROI_get_bbox = False 
py_name = 'vott_tracker' 
log_path = '../../Drone_Project/Drone_Target/for_python_path.log'
data_for_next_json_file = []
track_success = True

class Worker(threading.Thread):
    def __init__(self, num, lock, cvtr, rvij, wvij, send_data, pym):
        threading.Thread.__init__(self)
        self.num = num 
        self.lock = lock
        self.cvtr = cvtr
        self.rvij = rvij
        self.wvij = wvij
        self.frame_counter = send_data[0]
        self.now_frame_timestamp_DP = send_data[1]
        self.bboxes = send_data[2]
        self.json_file_path = send_data[3]
        self.pym = pym
    def run(self):
        try:
            self.pym.PY_LOG(False, 'D', py_name, "Worker num:%d __run__" % self.num)
            self.lock.acquire()
            now_format = self.cvtr.get_now_format_value(self.frame_counter)
            deal_with_name_format_path(self.wvij, self.cvtr, self.now_frame_timestamp_DP, now_format)
            deal_with_BX_PT(self.wvij, self.bboxes) 
            self.wvij.create_id_asset_json_file(self.json_file_path)
            self.lock.release()
        except:
            self.pym.PY_LOG(True, 'E', py_name, "Worker num:%d failed" % self.num)
            

def fill_parent_and_tags_to_write_json(rvij, wvij):
    
    wvij.save_parent_id(rvij.get_parent_id())
    wvij.save_parent_name(rvij.get_parent_name())
    wvij.save_parent_path(rvij.get_parent_path())
    
    wvij.save_tags(rvij.get_tags())

    pym.PY_LOG(False, 'D', py_name , 'fill parent data and tags ok')

  
def deal_with_name_format_path(wvij, cvtr, now_frame_timestamp_DP, now_format): 
    
    pym.PY_LOG(False, 'D', py_name, 'now_frame_timestamp_DP: %.6f' % now_frame_timestamp_DP)
    pym.PY_LOG(False, 'D', py_name, 'now_fromat: %s' % now_format)

    org_asset_name, org_timestamp, org_asset_path = get_data_for_next_json_file()
    pym.PY_LOG(False, 'D', py_name, 'org_asset_name: %s' % org_asset_name)
    pym.PY_LOG(False, 'D', py_name, 'org_timestamp: %.5f' % org_timestamp)
    pym.PY_LOG(False, 'D', py_name, 'org_asset_path: %s' % org_asset_path)
    
    org_timestamp = int(org_timestamp)
    
    name_count = org_asset_name.find('=')
    org_asset_name = org_asset_name[:name_count+1]
    now_timestamp = now_frame_timestamp_DP
    now_timestamp = str(org_timestamp +  now_timestamp)
    now_asset_name = org_asset_name + now_timestamp
    pym.PY_LOG(False, 'D', py_name, 'now_frame_asset_name: %s' % now_asset_name)
    pym.PY_LOG(False, 'D', py_name, 'now_timestamp: %s' % now_timestamp)
    
    path_count = org_asset_path.find('=')
    org_asset_path = org_asset_path[:path_count+1]     
    now_asset_path = org_asset_path + now_timestamp
    pym.PY_LOG(False,'D', py_name, 'now_frame_asset_path: %s' % now_asset_path)

    cmp_tp = cvtr.get_every_second_last_frame_timestamp()
    pym.PY_LOG(False,'D', py_name, 'cmp_tp: %s' % str(cmp_tp))
    if cmp_tp == now_frame_timestamp_DP:
        # if vott video fps = 15, cmp_tp = 0.933333
        deal_with_data_for_next_json_file(org_asset_name, org_timestamp, org_asset_path)

    #this function will be created id via path by md5 method 
    wvij.save_asset_path(now_asset_path)
    wvij.save_asset_format(now_format)
    wvij.save_asset_name(now_asset_name)
    wvij.save_timestamp(now_timestamp)


def deal_with_BX_PT(wvij, bboxes): 
    BX = [0,0,0,0]
    PT = [0,0]
    for i, bbox in enumerate(bboxes):
        BX[0] = bbox[3]  # height BX[0]
        BX[1] = bbox[2]  # width BX[1]
        BX[2] = bbox[0]  # left BX[2]
        BX[3] = bbox[1]  # top BX[3]
        PT[0] = BX[1]+BX[2]
        PT[1] = BX[0]+BX[3]
        wvij.save_boundingBox(BX, i)
        wvij.save_points(PT, i)

def shut_down_log(pym, rvij, wvij, cvtr):
    global track_success
    pym.PY_LOG(True, 'D', py_name, '__done___')
    rvij.shut_down_log('__done__')
    wvij.shut_down_log('__done__')
    cvtr.shut_down_log('__done__\n\n\n\n')
    #os.remove(log_path)
    if track_success:
        messagebox.showinfo("vott tracker", "tracking objects successfully!!")
    else:
        messagebox.showinfo("vott tracker", "tracking objects failed!!")
    sys.exit()

def RVIJ_class_new_and_initial(json_file_path):
    # get video's time that VoTT user to label track object 
    timestamp = 0

    # class rvij that is about reading data from json file
    rvij = RVIJ.read_vott_id_json(json_file_path)
    
    # read data
    rvij.read_from_id_json_data()

    timestamp = rvij.get_timestamp()

    update_data_for_next_json_file(rvij.get_asset_name() , \
                                    rvij.get_timestamp() , \
                                    rvij.get_asset_path())

    # get bounding box position
    bbox = rvij.get_boundingBox()
    return rvij, timestamp, bbox


def update_data_for_next_json_file(asset_name, timestamp, asset_path):
    global data_for_next_json_file 
    data_for_next_json_file = []
    data_for_next_json_file.append(asset_name)
    pym.PY_LOG(False, 'D', py_name, '(update_data_for_next_json_file) asset name: %s' % asset_name)
    data_for_next_json_file.append(timestamp)
    pym.PY_LOG(False, 'D', py_name, '(update_data_for_next_json_file) timestamp: %s' % timestamp)
    data_for_next_json_file.append(asset_path)
    pym.PY_LOG(False, 'D', py_name, '(update_data_for_next_json_file) asset_path: %s' % asset_path)


def deal_with_data_for_next_json_file(org_asset_name, org_timestamp, org_asset_path):
    prv_timestamp = int(org_timestamp) + 1
    pym.PY_LOG(False, 'D', py_name, '(deal_with_data_for_next_json_file) previous timestamp: %s' % str(prv_timestamp))
   
    index = org_asset_name.find('=')
    temp = org_asset_name[:index+1]
    prv_asset_name = temp + str(prv_timestamp)
    pym.PY_LOG(False, 'D', py_name, '(deal_with_data_for_next_json_file) previous asset name: %s' % prv_asset_name)

    index = org_asset_path.find('=')
    temp = org_asset_path[:index+1]
    prv_asset_path = temp + str(prv_timestamp)
    pym.PY_LOG(False, 'D', py_name, '(deal_with_data_for_next_json_file) previous asset path: %s' % prv_asset_path)

    update_data_for_next_json_file(prv_asset_name, prv_timestamp, prv_asset_path)

def get_data_for_next_json_file():
    global data_for_next_json_file
    asset_name = data_for_next_json_file[0]
    timestamp = data_for_next_json_file[1]
    asset_path = data_for_next_json_file[2]
    return asset_name, timestamp, asset_path

def CVTR_class_new_and_initial(algorithm, video_path, timestamp, bboxes, vott_video_fps):
    # class cvtr that is about VoTT openCV tracker settings
    
    # debug mode
    # pos0: show video with bbox             
    # pos1: save image with bbox             
    # pos2: save viedo with bbox     
    # ROI_get_bbox just a tester to test tracking function
    image_debug = [1, 0, 0]
    cvtr = CVTR.CV_TRACKER(algorithm, video_path, timestamp, bboxes, image_debug, vott_video_fps)
    return cvtr


def WVIJ_class_new_and_initial(target_path):
    # class wvij that is about writing data to json file  
    
    wvij = WVIJ.write_vott_id_json(target_path)

    return wvij

def get_loop_number_and_judge_interval(cvtr, vott_video_fps):
    source_video_fps = cvtr.get_source_video_fps()
    pym.PY_LOG(False, 'D', py_name, 'source_video_fps: %d' % source_video_fps)

    loop_num_interval = float(source_video_fps / vott_video_fps)
    pym.PY_LOG(False, 'D', py_name, 'loop number interval : %.2f' % loop_num_interval)
    return source_video_fps, loop_num_interval


def deal_with_data_saveto_newJsonFile(frame_counter, now_frame_timestamp_DP, \
                                        bboxes, json_file_path):                       
    # dealing with data and saving to a new json file
    send_data = []
    send_data.append(frame_counter)
    send_data.append(now_frame_timestamp_DP)
    send_data.append(bboxes)
    send_data.append(json_file_path)
    return send_data
 
def main(target_path, json_file_path, video_path, algorithm, other_paras):
    global track_success 
    vott_video_fps = 15

    # initial class RVIJ
    rvij, timestamp, bboxes = RVIJ_class_new_and_initial(json_file_path)

    # initial class CVTR
    cvtr = CVTR_class_new_and_initial(algorithm, video_path, timestamp, bboxes, vott_video_fps)
    
    # initial class WVIJ
    wvij = WVIJ_class_new_and_initial(target_path) 

    # saving some data from json file for into new json file using 
    fill_parent_and_tags_to_write_json(rvij, wvij)

    # reading and setting
    frame_counter = cvtr.get_label_frame_number(rvij.get_asset_format())

    pym.PY_LOG(False, 'D', py_name, 'user to label frame number: %d' % frame_counter)
  
    # get soure_video_fps and loop_num_interval 
    source_video_fps, loop_num_interval = get_loop_number_and_judge_interval(cvtr, vott_video_fps)
    
    # for saving data to json file
    json_file_lock = threading.Lock()  

    for tt in range(tracking_time):
        # for saving data to json file
        thread_counter = 0
        thread_list = []
        
        if tt > 0:
            if tt == 1:
                pym.PY_LOG(False, 'D', py_name, 'first loop over')
            frame_counter = -1

        first_loop_counter, loop_num = cvtr.get_loop_counter_and_loop_num(frame_counter)
        pym.PY_LOG(False, 'D', py_name, 'first_loop_counter: %d' % first_loop_counter)

        for loop_counter in range(first_loop_counter, source_video_fps+1):
            try:
                frame = cvtr.capture_video_frame()
                if loop_counter >= loop_num and loop_counter <= loop_num + 1:
                    # first loop at most only pick up 14 frames (frist frame is user using vott to track object) from source video frames
                    frame_counter += 1
                    loop_num = loop_num + loop_num_interval
                    if frame_counter < vott_video_fps:                 
                        pym.PY_LOG(False, 'D', py_name, 'frame_counter: %d start' % frame_counter)
                        now_frame_timestamp_DP = cvtr.get_now_frame_timestamp_DP(frame_counter)
                        pym.PY_LOG(False, 'D', py_name, '(main) now_frame_timestamp_DP: %.6f' % now_frame_timestamp_DP)
                        bboxes, track_success = cvtr.draw_boundbing_box_and_get(frame)
                        print('test1')
                        if track_success == False:
                            break
                        # dealing with data and saving to a new json file
                        send_data = deal_with_data_saveto_newJsonFile(frame_counter, \
                                                            now_frame_timestamp_DP, \
                                                            bboxes, json_file_path) 

                        thread_list.append(Worker(thread_counter, json_file_lock, cvtr, rvij, wvij, send_data, pym))
                        thread_list[thread_counter].start()
                        thread_counter += 1

            except:
                pym.PY_LOG(False, 'E', py_name, 'main loop has wrong condition!!')
                track_success = False
                cvtr.destroy_debug_window()
                for i in range(thread_counter):
                    thread_list[i].join()
                shut_down_log(pym, rvij, wvij, cvtr)
                break

        for i in range(thread_counter):
            # run 1 tt loop, delete all threads
            thread_list[i].join()
        
        if track_success == False:
            break
    shut_down_log(pym, rvij, wvij, cvtr)

def read_file_name_path_from_vott_log(target_path):
    # file ex:
    # file:/home/ivan/HD1/hd/VoTT/Drone_Project/Drone_Source/001/Drone_001.mp4#t=305.533333,76a8e999e2d9232d8e26253551acb4b3-asset.json,time

    if os.path.exists(target_path):
        pym.PY_LOG(False, 'D', py_name, 'target_path: %s existed!' % target_path)                                                                         
    else:
        pym.PY_LOG(False, 'E', py_name, 'target_path: %s is not existed!' % target_path)
        sys.exit()
        return False, "","","",""

    f = open(target_path, "r") 
    # remove file:
    path = f.read()
    path = path[5:]
    vc = 0
    
    # get source video path
    vc = path.find('#')
    video_path = path[:vc]
    pym.PY_LOG(False, 'D', py_name, 'video_path: %s' % video_path)

    # get json file(this file will be created when user used vott to label object)
    vc = path.find(',')
    file_name = path[vc+1:]
    pym.PY_LOG(False, 'D', py_name, 'file_name with time: %s' % file_name)

    # get tracking_time
    tracking_time = 1
    vc_tt = file_name.find(',')
    temp = file_name[vc_tt+1:]
    vc_tt = temp.find(',')
    tracking_time = int(temp[vc_tt+1:])
    pym.PY_LOG(False, 'D', py_name, 'tracking_time: %d' % tracking_time)
     

    vc = file_name.find(',')
    file_name = file_name[:vc]
    pym.PY_LOG(False, 'D', py_name, 'file_name without time: %s' % file_name)
    
    # replace Dorne_Source to Drone_Target because from video path,
    # because we need to get the json file at Drone_Target/target_name folder
    # please note if users target_name(ex:001) folder is not equal to source_name(ex:001) 
    # below target_path will be wrong!!!
    target_path = video_path.replace("Drone_Source", "Drone_Target")
    l1 = target_path.find("Drone_Target")
    l2 = l1 + len("Drone_Target/")
    temp_path = target_path[l2:]
    l3 = temp_path.find('/')
    last_dir_path = temp_path[:l3] 
    target_path = target_path[:l2] + last_dir_path + '/'
    pym.PY_LOG(False, 'D', py_name, 'target_path: %s' % target_path)
    json_file_path = target_path + file_name
    pym.PY_LOG(False, 'D', py_name, 'json_file_path: %s' % json_file_path)
    return True, video_path, target_path, json_file_path, tracking_time



if __name__ == '__main__':
    # below(True) = exports log.txt
    pym = PYM.LOG(True)  
    other_paras = []
    vott_log_ok, video_path, target_path, json_file_path, tracking_time= read_file_name_path_from_vott_log(log_path)
    other_paras.append(tracking_time)
    #if len(sys.argv[1]) > 1:
        #file_path = file_path + sys.argv[1]
        #print("file_path: %s" % file_path)
    #if len(sys.argv[2]) > 1:
        #algorithm = sys.argv[2]
        #print(algorithm)

    arrived_next_frame = False 
    algorithm = 'CSRT'
    if vott_log_ok:
        main(target_path, json_file_path, video_path, algorithm, other_paras)
