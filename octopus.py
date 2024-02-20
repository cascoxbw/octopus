from handbook import handbook
from util import util as u
from case import case

class octopus:
    def __init__(self):
        self.handbook = handbook().get()
        self.case_list = self.load()

    # def platform(self):
    #     try:
    #         with open(self.handbook['env'], 'r') as file:
    #             if 'spr' in file.read():
    #                 plat = 'SPR-EE'
    #             else:
    #                 plat = 'ICX-SP'
    #         print("platform: ",plat)
    #         return plat
    #     except:
    #         print('platform error')
        
    def env(self):
        print("[env set]")
        oneapi = u.source(self.handbook['oneapi'])
        oneapiIn = f"{oneapi} &> /dev/null"
        env = u.source(self.handbook['env'])
        u.execute(oneapiIn,env)

    def load(self):
        if self.handbook['is_flex']:
            return [case(id,self.handbook) for id in self.handbook['flex']]
        else:
            return [case(id,self.handbook) for id in range(0,self.handbook['active_case_num'])]

    def check(self):
        u.fence('summary')
        print("platform: ",self.handbook['platform'])
        print("algo: ",self.handbook['algo'])

        passCount = 0
        failCount = 0
        for case in self.case_list:
            print(f"{case.name}: {case.result}")
            if case.isPass:
                passCount+=1
            else:
                failCount+=1
        u.fence('total:',self.handbook['active_case_num'],'pass:',passCount,'fail:',failCount)

    def execute(self):
        self.env()
        console = None
        self.case_list[0].clean()
        for case in self.case_list:
            console = case.execute(console)
        self.case_list[-1].clean()
        self.check()











if __name__ == "__main__":
    octopus().execute()