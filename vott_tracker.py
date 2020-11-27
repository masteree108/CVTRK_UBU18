import os
import sys
import read_vott_id_json as RVIJ
import write_vott_id_json as WVIJ
import cv_tracker as CVTR
import process_project_vott as PPV 
import log as PYM
from vott_tracker_func import*
import threading

class Worker(threading.Thread):
    def __init__(self, num, lock, cvtr, rvij, ppv, wvij, send_data, pym):
        threading.Thread.__init__(self)
        self.num = num 
        self.lock = lock
        self.cvtr = cvtr
        self.rvij = rvij
        self.wvij = wvij
        self.ppv = ppv
        self.frame_counter = send_data[0]
        self.bboxes = send_data[1]
        self.json_file_path = send_data[2]
        self.update_state = send_data[3]
        self.pym = pym

    def run(self):
        try:
            self.pym.PY_LOG(False, 'D', py_name, "Worker num:%d __run__" % self.num)
            self.lock.acquire()
            deal_with_name_format_path(self.wvij, self.cvtr, self.ppv, self.frame_counter, self.update_state)
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

  
def deal_with_name_format_path(wvij, cvtr, ppv, frame_counter, update_state): 
    
    now_frame_timestamp_DP = cvtr.get_now_frame_timestamp_DP(frame_counter)
    now_format = cvtr.get_now_format_value(frame_counter)
    pym.PY_LOG(False, 'D', py_name, 'now_frame_timestamp_DP: %.6f' % now_frame_timestamp_DP)
    pym.PY_LOG(False, 'D', py_name, 'now_fromat: %s' % now_format)

    prv_asset_name, prv_timestamp, prv_asset_path = get_previous_data_for_next_json_file()
    pym.PY_LOG(False, 'D', py_name, 'previous_asset_name: %s' % prv_asset_name)
    pym.PY_LOG(False, 'D', py_name, 'previous_timestamp: %.5f' % prv_timestamp)
    pym.PY_LOG(False, 'D', py_name, 'previous_asset_path: %s' % prv_asset_path)
    
    prv_timestamp_bf_DP = 0
    if update_state:
        pym.PY_LOG(False, 'D', py_name, 'update(timestamp+1)')
        prv_timestamp_bf_DP = int(prv_timestamp) + 1
    else:
        prv_timestamp_bf_DP = int(prv_timestamp)
    pym.PY_LOG(False, 'D', py_name, 'prv_timestamp_bf_DP: %d' % prv_timestamp_bf_DP)

    name_count = prv_asset_name.find('=')
    prv_asset_name = prv_asset_name[:name_count+1]
        
    now_timestamp = prv_timestamp_bf_DP + now_frame_timestamp_DP
    now_asset_name = prv_asset_name + str(now_timestamp)
    pym.PY_LOG(False, 'D', py_name, 'now_frame_asset_name: %s' % now_asset_name)
    pym.PY_LOG(False, 'D', py_name, 'now_timestamp: %.5f' % now_timestamp)
    
    path_count = prv_asset_path.find('=')
    prv_asset_path = prv_asset_path[:path_count+1]     
    now_asset_path = prv_asset_path + str(now_timestamp)
    pym.PY_LOG(False,'D', py_name, 'now_frame_asset_path: %s' % now_asset_path)

    # update previous data 
    deal_with_data_for_next_json_file(now_asset_name, now_timestamp, now_asset_path)

    #this function will be created id via path by md5 method 
    wvij.save_asset_path(now_asset_path)
    wvij.save_asset_format(now_format)
    wvij.save_asset_name(now_asset_name)
    wvij.save_timestamp(now_timestamp)
        
    # package data for writing to project.vott
    md5_id = wvij.get_asset_md5_id()
    ppv.package_data_for_writing_to_project_vott(md5_id, now_format, now_asset_name, now_asset_path, now_timestamp)

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

def PPV_class_new_and_initial(target_path, project_vott_file_path, rvij):
    # default fps
    fps = 15 
    ppv = PPV.process_project_vott(target_path, project_vott_file_path, rvij.get_asset_id())
    if ppv.check_file_exist() == False:
        rvij.shut_down_log('process_terminate')
        shutdown_log_and_show_error_msg("class process_project_vott failed!!", False)
    else:
        fps = ppv.read_fps()
    return fps, ppv

def RVIJ_class_new_and_initial(json_file_path):
    # get video's time that VoTT user to label track object 
    timestamp = 0

    # class rvij that is about reading data from json file
    rvij = RVIJ.read_vott_id_json(json_file_path)
  
    # check file exist?
    if rvij.check_file_exist() == False:
        shutdown_log_and_show_error_msg("class read_vott_id_json failed!!", True)
    else:
        # read data
        read_id_ok, state = rvij.read_data_from_id_json_data()
        if read_id_ok == False: 
            if state == 'no_id':
                # there are no added ID on the VoTT
                shutdown_log_and_show_error_msg("no added ID on the VoTT!!", True)
                            
            elif state == 'same_id': 
                shutdown_log_and_show_error_msg("gave same ID on the VoTT!!", True)
                            
        else:
            timestamp = rvij.get_timestamp()

            update_previous_data_for_next_json_file(rvij.get_asset_name() , \
                                            rvij.get_timestamp() , \
                                            rvij.get_asset_path())

            # get bounding box position
            bbox = rvij.get_boundingBox()
            return rvij, timestamp, bbox


def update_previous_data_for_next_json_file(asset_name, timestamp, asset_path):
    global previous_data 
    previous_data = []
    previous_data.append(asset_name)
    pym.PY_LOG(False, 'D', py_name, '(update_previous_data_for_next_json_file) asset name: %s' % asset_name)
    previous_data.append(timestamp)
    pym.PY_LOG(False, 'D', py_name, '(update_previous_data_for_next_json_file) timestamp: %s' % timestamp)
    previous_data.append(asset_path)
    pym.PY_LOG(False, 'D', py_name, '(update_previous_data_for_next_json_file) asset_path: %s' % asset_path)


def deal_with_data_for_next_json_file(prv_asset_name, prv_timestamp, prv_asset_path):
    pym.PY_LOG(False, 'D', py_name, '(deal_with_data_for_next_json_file) previous timestamp: %.5f' % prv_timestamp)
   
    index = prv_asset_name.find('=')
    temp = prv_asset_name[:index+1]
    prv_asset_name = temp + str(prv_timestamp)
    pym.PY_LOG(False, 'D', py_name, '(deal_with_data_for_next_json_file) previous asset name: %s' % prv_asset_name)

    index = prv_asset_path.find('=')
    temp = prv_asset_path[:index+1]
    prv_asset_path = temp + str(prv_timestamp)
    pym.PY_LOG(False, 'D', py_name, '(deal_with_data_for_next_json_file) previous asset path: %s' % prv_asset_path)

    update_previous_data_for_next_json_file(prv_asset_name, prv_timestamp, prv_asset_path)

def get_previous_data_for_next_json_file():
    global previous_data
    asset_name = previous_data[0]
    timestamp = previous_data[1]
    asset_path = previous_data[2]
    return asset_name, timestamp, asset_path

def CVTR_class_new_and_initial(algorithm, video_path, timestamp, bboxes, rvij, ppv, vott_video_fps):
    # class cvtr that is about VoTT openCV tracker settings
    
    # debug mode
    # pos0: show video with bbox             
    # pos1: save image with bbox             
    # pos2: save viedo with bbox     
    # ROI_get_bbox just a tester to test tracking function
    image_debug = [1, 0, 0]
    
    # 1. initial
    cvtr = CVTR.CV_TRACKER(video_path)
    
    # 2. opencv setting
    if cvtr.opencv_setting(algorithm, timestamp, bboxes, image_debug) == False:
        msg = "opencv setting failed"
        cvtr.destroy_debug_window()
        rvij.shut_down_log('process_terminate')
        ppv.shut_down_log('process_terminate')
        cvtr.shut_down_log('process_terminate\n\n\n\n')
        shutdown_log_and_show_error_msg(msg, True)
     
    # 3. check fps from project.vott
    if cvtr.check_support_fps(vott_video_fps) == False:
        msg = "this FrameExtractionRate: %d that user setted on the Vott is not support!!" % vott_video_fps
        cvtr.destroy_debug_window()
        rvij.shut_down_log('process_terminate')
        ppv.shut_down_log('process_terminate')
        cvtr.shut_down_log('process_terminate\n\n\n\n')
        shutdown_log_and_show_error_msg(msg, True)

    return cvtr


def WVIJ_class_new_and_initial(target_path):
    # class wvij that is about writing data to json file  
    
    wvij = WVIJ.write_vott_id_json(target_path)
    if wvij.check_file_exist() == False:
        shutdown_log_and_show_error_msg("class write_vott_id_json failed!!", True)
    else:
        return wvij


def deal_with_data_saveto_newJsonFile(frame_counter, bboxes, json_file_path, update_state):
    # dealing with data and saving to a new json file
    send_data = []
    send_data.append(frame_counter)
    send_data.append(bboxes)
    send_data.append(json_file_path)
    send_data.append(update_state)
    return send_data

def shutdown_log_and_show_error_msg_with_rvij(msg, rvij, remove_switch):
    paras = []
    paras.append(msg)
    paras.append(pym)
    paras.append(remove_switch)
    paras.append(vott_source_info_path)
    paras.append(vott_target_path)
    do_shutdown_log_and_show_error_msg(paras)


def shutdown_log_and_show_error_msg(msg, remove_switch):
    paras = []
    paras.append(msg)
    paras.append(pym)
    paras.append(remove_switch)
    paras.append(vott_source_info_path)
    paras.append(vott_target_path)
    do_shutdown_log_and_show_error_msg(paras)

def shutdown_log_with_all(msg, pym, rvij, ppv, wvij, cvtr):
    paras = []
    global track_success
    paras.append(msg)
    paras.append(track_success)
    paras.append(vott_source_info_path)
    paras.append(vott_target_path)
    do_shutdown_log_with_all(pym, rvij, ppv, wvij, cvtr, paras)

def main(target_path, project_vott_file_path,  json_file_path, video_path, algorithm, main_paras):
    global track_success

    tracking_time = main_paras[0]
    
    # initial class RVIJ
    rvij, timestamp, bboxes = RVIJ_class_new_and_initial(json_file_path)
    
    #initial class PPV(read fps that user setted on the VoTT project)
    vott_video_fps, ppv= PPV_class_new_and_initial(target_path, project_vott_file_path, rvij)

    # initial class CVTR
    cvtr = CVTR_class_new_and_initial(algorithm, video_path, timestamp, bboxes, rvij, ppv, vott_video_fps)
        
    # initial class WVIJ
    wvij = WVIJ_class_new_and_initial(target_path) 

    # saving some data from json file for into new json file using 
    fill_parent_and_tags_to_write_json(rvij, wvij)

    # reading and setting
    frame_counter = cvtr.get_label_frame_number(rvij.get_asset_format())
    pym.PY_LOG(False, 'D', py_name, 'user to label frame number: %d' % frame_counter)
    # +1 because we don't need this frame that is our labeled on the VoTT
    frame_counter = frame_counter + 1

    # get soure_video_fps and loop_num_interval 
    #source_video_fps, loop_num_interval = get_loop_number_and_judge_interval(cvtr, vott_video_fps)
    source_video_fps = cvtr.get_source_video_fps()
    pick_up_frame_interval = cvtr.get_pick_up_frame_interval(vott_video_fps)
    pym.PY_LOG(False, 'D', py_name, 'pick_up_frame_interval: %d' % pick_up_frame_interval)
    
    # for saving data to json file
    json_file_lock = threading.Lock()  


    for tt in range(tracking_time):
        # for saving data to json file
        thread_counter = 0
        thread_list = []
        update_state = False
        if tt > 0:
            if tt == 1:
                pym.PY_LOG(False, 'D', py_name, '--------------first loop over-----------------\n')
            frame_counter = 1

        loop_start_frame = int((frame_counter-1) * pick_up_frame_interval)
        pym.PY_LOG(False, 'D', py_name, 'loop_start_frame: %d' % loop_start_frame)
        pick_up_frame = int(frame_counter * pick_up_frame_interval)
        pym.PY_LOG(False, 'D', py_name, 'start pick up frame: %d' % pick_up_frame)

        for loop_counter in range(loop_start_frame, source_video_fps+1):
            try:
                frame = cvtr.capture_video_frame()
                if loop_counter == pick_up_frame-1:
                    # first loop at most only pick up (vott_vidoe_fps-1) frames (frist frame is user using vott to track object) from source video frames
                    if frame_counter == 1 and tt > 0:
                        update_state = True
                    else:
                        update_state = False
                    pick_up_frame = pick_up_frame + pick_up_frame_interval
                    pym.PY_LOG(False, 'D', py_name, '\n frame_counter: %d start' % frame_counter)
                    bboxes, track_success = cvtr.draw_boundbing_box_and_get(frame, rvij.get_ids())
                    if track_success == False:
                        break
                    # dealing with data and saving to a new json file
                    send_data = deal_with_data_saveto_newJsonFile(frame_counter, \
                                                            bboxes, json_file_path, update_state)

                    thread_list.append(Worker(thread_counter, json_file_lock, cvtr, rvij, ppv, wvij, send_data, pym))
                    thread_list[thread_counter].start()
                    thread_counter += 1
                    frame_counter += 1

            except:
                pym.PY_LOG(False, 'E', py_name, 'main loop has wrong condition!!')
                track_success = False
                cvtr.destroy_debug_window()
                for i in range(thread_counter):
                    thread_list[i].join()
                
                shutdown_log_with_all("process terminate", pym, rvij, ppv, wvij, cvtr)
                break

        for i in range(thread_counter):
            # run 1 tt loop, delete all threads
            thread_list[i].join()
        
        if track_success == False:
            break

    # writing data that we tracked into project.vott  
    ppv.write_data_to_project_vott()
    ppv.write_tmp_data_for_vott_using()
    shutdown_log_with_all("__done__", pym, rvij, ppv, wvij, cvtr)


if __name__ == '__main__':
    # ===========  Global variables set area start ==============
    ROI_get_bbox = False 
    py_name = '< vott_tracker >' 
    vott_source_info_path = ''
    #ex: vott_source_info_path = '../../../Drone_Target/vott_source_info.tmp'
    vott_target_path = ''
    #ex vott_target_path = '../../../Drone_Target/vott_target_path.json'

    previous_data = []
    track_success = True

    paras = []
    main_paras = []
    # below(True) = exports log.txt
    pym = PYM.LOG(True) 
    # ===========  Global variables set area over==============

    pym.PY_LOG(False, 'D', py_name, 'vott_tracker.exe version: v0.0.3_unstable')

    # reading parameter from user pressing vott "auto track" button
    get_para_ok = True
    try:
        if len(sys.argv[1]) > 1:
            vott_source_info_path = sys.argv[1]
        if len(sys.argv[2]) > 1:
            vott_target_path = sys.argv[2]
        pym.PY_LOG(False, 'D', py_name, 'get vott_source_info_path: %s from vott created' % vott_source_info_path)
        pym.PY_LOG(False, 'D', py_name, 'vott_target_path: %s from vott created' % vott_target_path)
    except:
        get_para_ok = False
        shutdown_log_and_show_error_msg("read parameter from vott failed!!", False)

    if get_para_ok:
        read_vott_source_info_ok, video_path, json_file_name, tracking_time = read_vott_source_info(vott_source_info_path, pym)
        if read_vott_source_info_ok:
            read_vott_target_path_ok, target_path, project_vott_file_path, json_file_path = read_vott_target_path(vott_target_path, json_file_name, pym)

        if read_vott_source_info_ok and read_vott_target_path_ok:
            algorithm = 'CSRT'
            main_paras.append(tracking_time)
            main(target_path, project_vott_file_path, json_file_path, video_path, algorithm, main_paras)
        else:
            shutdown_log_and_show_error_msg("read vott_source_info or read_vott_target_failed!!", False)
