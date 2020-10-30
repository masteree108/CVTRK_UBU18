import os, shutil
import json
import hashlib
# pip install shortuuid
import shortuuid
import enum
import log as PYM

class BBOX_ITEM(enum.Enum):
    height = 0 
    width = 1                                                                                                                                
    left = 2 
    top = 3   
                
class POINT_ITEM(enum.Enum):
    x2 = 0    
    y2 = 1   

class write_vott_id_json():
# private
    
    __asset_id = ""
    __asset_format = ""
    __asset_path = ""

    __parent_id = ""
    __parent_name = ""
    __parent_path = ""

    __video_size = [3840, 2160]
    __timestamp = 0
        
    __regions_id = ""
    __tags = []
    __boundingBox = []
    __points = []

    def __save_asset_id(self, sid):
        self.__asset_id = sid

    def __save_regions_id(self, rid):
        self.__regions_id = rid

    def __create_asset_id_via_md5(self, path):
        m = hashlib.md5()
        m.update(path.encode("utf-8"))
        h = m.hexdigest()
        self.pym.PY_LOG(False, 'D', self.__class__, 'via md5 to create asset_id: %s' % h)
        self.__save_asset_id(h)

    def __create_shorid_for_regions_id(self):
        sid = shortuuid.uuid()
        sid = sid[:9]
        self.__save_regions_id(sid)

# public
    def __init__(self, target_path):
        # below(True) = exports log.txt
        self.pym = PYM.LOG(True)
        self.target_path = ""
        if os.path.exists(target_path):
            self.__target_path = target_path
            self.pym.PY_LOG(False, 'D', self.__class__, 'traget_path: %s is existed' % target_path)
        else:
            self.pym.PY_LOG(False, 'E', self.__class__, 'traget_path: %s is not existed!!' % target_path)
    
    #del __del__(self):
        #deconstructor  
    
    def create_id_asset_json_file(self, json_file_path):
        try:
            #self.__create_shorid_for_regions_id()
            new_json_file_path = self.__target_path + self.__asset_id + '-asset.json'
            self.pym.PY_LOG(False, 'D', self.__class__, 'new json file_path: %s' % new_json_file_path)
            shutil.copyfile(json_file_path, new_json_file_path); 
            # open and modify content 
            with open( new_json_file_path, 'r+') as f:
                data = json.load(f)
                data['asset']['id'] = self.__asset_id
                data['asset']['format'] = self.__asset_format 
                data['asset']['name'] = self.__asset_name
                data['asset']['path'] = self.__asset_path
 
                #data['asset']['parent']['id'] = self.__parent_id
                #data['asset']['parent']['name'] = self.__parent_name
                #data['asset']['parent']['path'] = self.__parent_path
 
                data['asset']['timestamp'] = self.__timestamp

                # dealing with part of regions
                self.__create_shorid_for_regions_id()
                
                for i in range(len(self.__boundingBox)):
                    data['regions'][i]['id'] = self.__regions_id

                    for j, tag_value in enumerate(self.__tags[i]):
                        data['regions'][i]['tags'][j] = tag_value

                    data['regions'][i]['boundingBox']["height"] = self.__boundingBox[i][0]
                    data['regions'][i]['boundingBox']["width"] = self.__boundingBox[i][1]
                    data['regions'][i]['boundingBox']["left"] = self.__boundingBox[i][2]
                    data['regions'][i]['boundingBox']["top"] = self.__boundingBox[i][3]
                    data['regions'][i]['points'][0]["x"] = self.__boundingBox[i][2]
                    data['regions'][i]['points'][0]["y"] = self.__boundingBox[i][3]
                
                    data['regions'][i]['points'][1]["x"] = self.__points[i][0]
                    data['regions'][i]['points'][1]["y"] = self.__boundingBox[i][3]
                
                    data['regions'][i]['points'][2]["x"] = self.__points[i][0]
                    data['regions'][i]['points'][2]["y"] = self.__points[i][1]
                
                    data['regions'][i]['points'][3]["x"] = self.__boundingBox[i][2]
                    data['regions'][i]['points'][3]["y"] = self.__points[i][1]

                f.close()
            os.remove(new_json_file_path)

            # save modified content 
            with open( new_json_file_path, 'w') as f:
                json.dump(data, f, indent = 4)
                f.close()
        except:
            self.pym.PY_LOG(False, 'E', self.__class__, 'write VoTT id json file failed!!')


    def save_asset_format(self, sformat):
        self.__asset_format = sformat
    
    def save_asset_name(self, sname):
        self.__asset_name = sname

    def save_asset_path(self, spath):
        self.__asset_path = spath
        self.__create_asset_id_via_md5(self.__asset_path)

    def save_parent_id(self, pid):
        self.__parent_id = pid

    def save_parent_name(self, pname):
        self.__parent_name = pname

    def save_parent_path(self, ppath):
        self.__parent_path = ppath

    def save_video_size(self, size):
        self.__video_size = size

    def save_timestamp(self, timestamp):
        self.__timestamp = timestamp
    
    def save_tags(self, tags):
        self.__tags = tags

    def save_boundingBox(self, BX, index):
        if index == 0:
            self.__boundingBox = [[0,0,0,0],]
        else:
            self.__boundingBox.append([0,0,0,0])
            
        self.__boundingBox[index][BBOX_ITEM.height.value] = BX[BBOX_ITEM.height.value]  #height 
        self.__boundingBox[index][BBOX_ITEM.width.value] = BX[BBOX_ITEM.width.value]  #width 
        self.__boundingBox[index][BBOX_ITEM.left.value] = BX[BBOX_ITEM.left.value]  #left
        self.__boundingBox[index][BBOX_ITEM.top.value] = BX[BBOX_ITEM.top.value]  #top

    def save_points(self, PT, index):
        # POINT x1 = left
        # POINT y1 = top
        if index == 0:
            self.__points = [[0,0],]
        else:
            self.__points.append([0,0])

        self.__points[index][POINT_ITEM.x2.value] = PT[POINT_ITEM.x2.value]  #x2
        self.__points[index][POINT_ITEM.y2.value] = PT[POINT_ITEM.y2.value]  #y2

    def shut_down_log(self, msg):
         self.pym.PY_LOG(True, 'D', self.__class__, msg)



