import os                   
import json
import log as PYM        

'''                                                                                                                                                         
data ex:
please note if the data is the last one, it's content's last symbol '}' doesn't need to add ','
assets:{
...
    "6ffccfa0b13d90525163a665f97eba43": {
            "id": "6ffccfa0b13d90525163a665f97eba43",
            "format": "666667",
            "state": 2,             ===>2=this frame already has labeled
            "type": 3,
            "name": "Drone_001.mp4#t=437.666667",
            "path": "file:/home/ivan/HD1/hd/Drone_Source/001/Drone_001.mp4#t=437.666667",
            "size": {
                "width": 3840,
                "height": 2160
            },
            "parent": {
                "format": "mp4",
                "id": "06d6c585b140585f176e0b9fa47fb4e5",
                "name": "Drone_001.mp4",
                "path": "file:/home/ivan/HD1/hd/Drone_Source/001/Drone_001.mp4",
                "size": {
                    "width": 3840,
                    "height": 2160
  },    
                "state": 2,
                "type": 2
            },
            "timestamp": 437.666667
        },
}
                                                                                                                                                    
bleow data which are we need to write to project.vott 
    "2b9b6ed156aba31625e8175a2e7f4772": {
            "id": "2b9b6ed156aba31625e8175a2e7f4772",
            "format": "733333",
            "name": ""Drone_001.mp4#t=437.733333",
            "path": "file:/home/ivan/HD1/hd/Drone_Source/001/Drone_001.mp4#t=437.733333",
            "timestamp": 437.733333
    }
'''



class process_project_vott():
# private
    __file_path = ''
    __log_name = '< class Process_Project_VoTT >'
    __label_id = ''
    __data_list = []
    __id_list = []
    __label_size = {}
    __label_parent = {}
    __json_content = ''
    __target_path = ''
    __track_data_path = ''

    def __open_file(self):
        f = open(self.__file_path, 'r')
        self.__json_content = json.loads(f.read())
        f.close()

    def __open_new_file(self):
        f = open(self.__track_data_path, 'w+')
        f.close()   

    def __read_size_and_parent(self):
        size = {'size': self.__json_content['assets'][self.__label_id]['size']}
        self.__label_size.update(size)                                                                                                              
        parent = {'parent': self.__json_content['assets'][self.__label_id]['parent']}
        self.__label_parent.update(parent)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'label data size: %s' % self.__label_size)
        self.pym.PY_LOG(False, 'D', self.__log_name, 'label data parent: %s' % self.__label_parent)

# public
    def __init__(self, target_path, file_path, label_id):
        #below(True) = exports log.txt
        self.pym = PYM.LOG(True)  
        self.__target_path = target_path
        self.pym.PY_LOG(False, 'D', self.__log_name, 'target_path: %s' % target_path)  
        self.__track_data_path = target_path + "track_data.json"
        self.pym.PY_LOG(False, 'D', self.__log_name, 'track_data.json path: %s' % self.__track_data_path)  
        if os.path.exists(self.__track_data_path):
            os.remove(self.__track_data_path)
        self.__file_path = file_path
        self.__label_id= label_id      

    def check_file_exist(self):
        if os.path.exists(self.__file_path):
            self.pym.PY_LOG(False, 'D', self.__log_name, '%s existed!' % self.__file_path)    
            return True
        else:
            self.pym.PY_LOG(True, 'E', self.__log_name, '%s is not existed!' % self.__file_path)
            return False

    def shut_down_log(self, msg):
        self.pym.PY_LOG(True, 'D', self.__log_name, msg)

    def show_data(self, asset_id, data):
        self.pym.PY_LOG(False, 'D', self.__log_name, 'asset_id(key): %s' % data[asset_id])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'id: %s' % data[asset_id]['id'])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'format: %s' % data[asset_id]['format'])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'name: %s' % data[asset_id]['name'])                                   
        self.pym.PY_LOG(False, 'D', self.__log_name, 'path: %s' % data[asset_id]['path'])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'size: %s' % data[asset_id]['size'])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'parent: %s' % data[asset_id]['parent'])
        self.pym.PY_LOG(False, 'D', self.__log_name, 'timestamp: %.6f' % data[asset_id]['timestamp'])

     
    def read_fps(self):
        self.__open_file()
        '''
        read ex:
        "videoSettings": {
            "frameExtractionRate": 5
        }, 
        '''
        
        fps = self.__json_content["videoSettings"]["frameExtractionRate"] 
        # this class will not use at the after step,so shut down save msg to log function
        # set PY_LOG(True...
        self.pym.PY_LOG(True, 'D', self.__log_name, 'get fps: %d' % fps)
        self.__read_size_and_parent()
        return fps  

    def package_data_for_writing_to_project_vott(self, asset_id, w_format, name, path, timestamp):
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'package asset_id: %s' % asset_id)
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'package format: %s' % w_format)
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'package name: %s' % name)
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'package path: %s' % path)
        #self.pym.PY_LOG(False, 'D', self.__log_name, 'package timestamp: %.6f' % timestamp)
        w_data = {asset_id: {'id':asset_id, 'format':w_format, 'state':2, 'type':3 \
                        ,'name':name, 'path':path}}
        timestamp = {'timestamp': timestamp}
        w_data[asset_id].update(self.__label_size)
        w_data[asset_id].update(self.__label_parent)
        w_data[asset_id].update(timestamp)
        self.__id_list.append(asset_id) 
        self.__data_list.append(w_data)

    def write_data_to_project_vott(self):
        for i, w_data in enumerate(self.__data_list):
            self.show_data(self.__id_list[i], w_data)
            self.__json_content['assets'].update(w_data)

        f = open(self.__file_path, 'w', newline='\n')
        new_json = json.dumps(self.__json_content, indent = 4)
        f.write(new_json)

    def write_tmp_data_for_vott_using(self):                  
        self.__open_new_file()                                
        f = open(self.__track_data_path, 'w', newline='\n')   
        new_json = json.dumps(self.__data_list, indent = 4)   
        f.write(new_json)                                     
