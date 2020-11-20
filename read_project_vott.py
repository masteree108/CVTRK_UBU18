import os                   
import json
import log as PYM        


class read_project_vott():
# private
    __file_path = ''
    __log_name = '< Read_Project_VoTT >'

# public
    def __init__(self, file_path):
        #below(True) = exports log.txt
        self.pym = PYM.LOG(True)  
        self.__file_path = file_path
    
    def check_file_exist(self):
        if os.path.exists(self.__file_path):
            self.pym.PY_LOG(False, 'D', self.__log_name, '%s existed!' % self.__file_path)    
            return True
        else:
            self.pym.PY_LOG(True, 'E', self.__log_name, '%s is not existed!' % self.__file_path)
            return False

    def read_fps(self):
        f = open(self.__file_path, 'r')
        json_content = json.loads(f.read())
        f.close()
        '''
        read ex:
        "videoSettings": {
            "frameExtractionRate": 5
        }, 
        '''
        
        fps = json_content["videoSettings"]["frameExtractionRate"] 
        # this class will not use at the after step,so shut down save msg to log function
        # set PY_LOG(True...
        self.pym.PY_LOG(True, 'D', self.__log_name, 'get fps: %d' % fps)    
        return fps 

