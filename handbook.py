from configparser import ConfigParser

class handbook:
    def __init__(self):
        self.cp = ConfigParser()
        self.name = 'handbook.ini'
        self.handbook = self.load()

    def load(self):
        try:
            self.cp.read(self.name)

            handbook = {}
            handbook['oneapi'] = self.cp['path']['oneapi']
            handbook['env'] = self.cp['path']['env']
            handbook['trex'] = self.cp['path']['trex']

            du = self.cp['path']['du']

            handbook['uesim'] = du + self.cp['path']['uesim']
            handbook['nr5g'] = du + self.cp['path']['nr5g']
            handbook['input'] = du + self.cp['path']['input']

            case_num = self.cp.getint('case', 'case_num')
            handbook['case_num'] = case_num
            
            handbook['case_list'] = [{'name':self.cp['case.'+str(i)]['name'],
                                      'trex_script_para':[para for para in self.cp['case.'+str(i)]['trex_script_para'].split(',')]} 
                                      for i in range(0,case_num)]

            handbook['output'] = self.cp['path']['output']
            return handbook
        except:
            print('load config error')

    def get(self):
        print(self.handbook)
        return self.handbook

