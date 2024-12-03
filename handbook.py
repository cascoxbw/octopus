from configparser import ConfigParser, ExtendedInterpolation
import os
import sys

class handbook:
    def __init__(self):
        self.cp = ConfigParser(interpolation=ExtendedInterpolation())
        self.name = 'handbook.ini'
        self.handbook = self.load()

    def load(self):
        try:
            # print(sys.path[0],os.path.dirname(__file__))

            handbook = {}
            handbook['self'] = os.path.dirname(__file__)
            handbook['du'] = os.path.abspath(os.path.join(handbook['self'],'../..'))
            handbook['uesim'] = os.path.join(handbook['du'],'project/build/uesim/')
            handbook['nr5g'] = os.path.join(handbook['du'],'project/build/nr5g/')
            handbook['input'] = os.path.join(handbook['du'],'project/config/benchmark/')
            handbook['output'] = os.path.join(handbook['self'],'output')

            self.cp.read(os.path.join(handbook['self'],self.name))
            
            handbook['oneapi'] = '/opt/intel/oneapi/setvars.sh'
            handbook['PATH'] = self.cp['env']['PATH']
            handbook['trex'] = self.cp['env']['trex']
            handbook['has_trex'] = os.path.exists(handbook['trex'])

            case_num = self.cp.getint('case', 'case_num')
            handbook['case_num'] = case_num
            handbook['active_case_num'] = case_num
            
            handbook['case_list'] = [{'name':self.cp['case.'+str(i)]['name'],
                                      'trex_script_para':[para for para in self.cp['case.'+str(i)]['trex_script_para'].split(',')],
                                      'algo':self.cp['case.'+str(i)]['dl_algo'] if 'dl_algo' in self.cp['case.'+str(i)] else 'su',
                                      'am':self.cp.getboolean('case.'+str(i),'am'),
                                      'group':self.cp['case.'+str(i)]['group']} 
                                      for i in range(0,case_num)]
            
            handbook['platform'] = self.cp['case']['platform']

            handbook['is_flex'] = self.cp.getboolean('case.flex', 'enable')
            if handbook['is_flex']:
                handbook['flex'] = [int(id) for id in self.cp['case.flex']['id'].split(',')]
                handbook['active_case_num'] = len(handbook['flex'])
            
            handbook['is_global'] = self.cp.getboolean('case.global', 'enable')
            if handbook['is_global']:
                handbook['global_algo'] = self.cp['case.global']['dl_algo']
                handbook['global_am'] = self.cp.getboolean('case.global','am')

            handbook['retry'] = 0 #self.cp.getint('case', 'retry_num')

            # handbook['ht'] = self.cp.getboolean('case', 'ht')

            handbook['duration'] = self.cp.getint('case', 'duration')

            handbook['dsa'] = self.cp.getboolean('case', 'dsa')

            return handbook
        except Exception as e:
            sys.exit(f'load handbook error:{e}')

    def get(self):
        # print(self.handbook)
        return self.handbook
