from configparser import ConfigParser, ExtendedInterpolation

class handbook:
    def __init__(self):
        self.cp = ConfigParser(interpolation=ExtendedInterpolation())
        self.name = 'handbook.ini'
        self.handbook = self.load()

    def load(self):
        try:
            self.cp.read(self.name)

            handbook = {}
            handbook['oneapi'] = self.cp['path']['oneapi']
            handbook['env'] = self.cp['path']['env']
            handbook['trex'] = self.cp['path']['trex']

            handbook['du'] = self.cp['path']['du']
            handbook['uesim'] = self.cp['path']['uesim']
            handbook['nr5g'] = self.cp['path']['nr5g']
            handbook['input'] = self.cp['path']['input']

            case_num = self.cp.getint('case', 'case_num')
            handbook['case_num'] = case_num
            handbook['active_case_num'] = case_num
            
            handbook['case_list'] = [{'name':self.cp['case.'+str(i)]['name'],
                                      'trex_script_para':[para for para in self.cp['case.'+str(i)]['trex_script_para'].split(',')],
                                      'algo':self.cp['case.'+str(i)]['algo']} 
                                      for i in range(0,case_num)]
            
            handbook['platform'] = self.cp['case']['platform']

            handbook['is_flex'] = self.cp.getboolean('case.flex', 'enable')
            if handbook['is_flex']:
                handbook['flex'] = [int(id) for id in self.cp['case.flex']['id'].split(',')]
                handbook['active_case_num'] = len(handbook['flex'])

            handbook['is_global_algo'] = self.cp.getboolean('case.algo', 'enable')
            handbook['global_algo'] = self.cp['case.algo']['name']

            handbook['retry'] = self.cp.getint('case', 'retry_num')
            
            handbook['output'] = self.cp['path']['output']
            return handbook
        except:
            print('load handbook error')

    def get(self):
        #print(self.handbook)
        return self.handbook

