from handbook import handbook
from util import util as u
from case import case

class octopus:
    def __init__(self):
        self.handbook = handbook().get()
        self.case_list = self.load()
        self.intervalCmd = 5

    # def platform(self):
    #     try:
    #         with open(self.handbook['env'], 'r') as file:
    #             if 'spr' in file.read():
    #                 plat = 'SPR-EE'
    #             else:
    #                 plat = 'ICX-SP'
    #         print('platform:',plat)
    #         return plat
    #     except:
    #         print('platform error')
    
    def ht(self,on):
        cmd = 'online' if on else 'offline'
        print(f'[ht {cmd}]')
        u.execute(f'./ht_onoffline.sh {cmd} &> /dev/null')
        u.sleep(self.intervalCmd)
        
    def env(self):
        print('[env set]')
        oneapi = u.source(self.handbook['oneapi'])
        oneapiIn = f'{oneapi} &> /dev/null'
        env = u.source(self.handbook['env'])
        u.execute(oneapiIn,env)

    def load(self):
        if self.handbook['is_flex']:
            return [case(id,self.handbook) for id in self.handbook['flex']]
        else:
            return [case(id,self.handbook) for id in range(0,self.handbook['active_case_num'])]

    def check(self):
        u.fence('summary')
        print('platform:',self.handbook['platform'])
        if self.handbook['is_global_algo']:
            print('global algo:',self.handbook['global_algo'])

        passCount = 0
        failCount = 0
        for case in self.case_list:
            if case.result[0]:
                passCount+=1
            else:
                failCount+=1
            print(f'{case.name}: {case.result[1]}')
        
        u.fence('total:',self.handbook['active_case_num'],'pass:',passCount,'fail:',failCount)

    def execute(self):
        self.env()
        self.ht(self.handbook['ht'])
        console = None
        self.case_list[0].clean()
        for case in self.case_list:
            console = case.execute(console)
        self.case_list[-1].clean()
        self.check()
        if self.handbook['ht'] == False:
            self.ht(True)











if __name__ == '__main__':
    octopus().execute()