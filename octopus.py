from handbook import handbook
from utils import utils as u
from tentacle import tentacle

class octopus:
    def __init__(self):
        self.handbook = handbook().get()
        self.case_list = self.load()
    
    # def ht(self,on):
    #     cmd = 'online' if on else 'offline'
    #     print(f'[ht {cmd}]')
    #     u.execute(f'./ht_onoffline.sh {cmd} &> /dev/null')

    def load(self):
        if self.handbook['is_flex']:
            return [tentacle(id,self.handbook) for id in self.handbook['flex']]
        else:
            return [tentacle(id,self.handbook) for id in range(0,self.handbook['active_case_num'])]

    def check(self):
        u.fence('summary')
        print('platform:',self.handbook['platform'])
        print('dsa:',self.handbook['dsa'])

        if self.handbook['is_global']:
            print('global algo:',self.handbook['global_algo'])
            print('global am:',self.handbook['global_am'])

        passCount = 0
        failCount = 0
        for case in self.case_list:
            if case.result[0]:
                passCount+=1
            else:
                failCount+=1
            print(f'id: {case.id}, case: {case.name} -> {case.result[1]}')
        
        u.fence('total:',self.handbook['active_case_num'],'pass:',passCount,'fail:',failCount)

    def execute(self):
        u.fence('octopus start')

        # self.ht(self.handbook['ht'])
        console = None
        cursor = 0
        self.case_list[cursor].clean()
        try:
            for i,case in enumerate(self.case_list):
                cursor = i
                console = case.execute(console)
        except Exception as e:
            print('case execute error:',e)
        self.case_list[cursor].clean()
        self.check()
        # self.ht(True)
            
        u.fence('octopus end')











if __name__ == '__main__':
    octopus().execute()