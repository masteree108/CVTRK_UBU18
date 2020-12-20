import os
import time
import platform

def get_created_time(file_path):
    # file ex:
    # Ubuntu:
    # file:/home/Drone_Source/Drone_001/Drone_001.mp4#t=305.533333,76a8e999e2d9232d8e26253551acb4b3-asset.json,time,tracking_time
    # Windows:
    # file:C:/Drone_Source/Drone_001/Drone_001.mp4#t=305.533333,76a8e999e2d9232d8e26253551acb4b3-asset.json,time,tracking_time
    #print("get_created_time start") 

    f = open(file_path, "r")
    path = f.read()
    f.close()
    path = path[5:]
    vc = 0                                                                                                                                                             
    #print(path) 
    # get source video path
    vc = path.find('#')
    video_path = path[:vc]
       
    # get json file(this file will be created when user used auto track function)
    vc = path.find(',')
    file_name = path[vc+1:]
    
    # get tracking_time       
    vc_tt = file_name.find(',')                 
    temp = file_name[vc_tt+1:]
    vc_tt = temp.find(',')
    #print(temp)
    created_time = temp[:vc_tt]
    #print(created_time)
    return int(created_time) 

def which_os():
    os_name = platform.system()
    #if os_name == 'Linux':
    #elif os_name == 'Windows':
    return os_name

def service_main():
    try:
        before_ctime = 0
        OS = which_os()
        print("OS:%s" % OS)
        if OS == 'Linux':
            os.system('./NTUT/exe/NTUT_version.exe')
        else:
            os.system("NTUT\\exe\\NTUT_version.exe")

        while(1):
            source_path = './vott_source_info.tmp'  
            target_path = './vott_target_path.json' 
            if os.path.exists(source_path) and os.path.exists(target_path):
                c_time = get_created_time(source_path)
                #print(c_time)
                if before_ctime < c_time:
                    if os.path.exists('./NTUT/exe/vott_tracker.exe'):
                        print("run exe")
                        if OS == 'Linux':
                            os.system("./NTUT/exe/vott_tracker.exe ./vott_source_info.tmp ./vott_target_path.json")
                        else:
                            os.system("NTUT\\exe\\vott_tracker.exe vott_source_info.tmp vott_target_path.json")
                        
                before_ctime = c_time
            time.sleep(0.01)
    except:
        print("error:service shutdown")

if __name__ == '__main__':
    service_main()
