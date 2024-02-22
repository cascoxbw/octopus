import os
import pexpect
import psutil
from handbook import handbook
from util import util as u
from case import case
from git import Repo

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
    
    def ht(self, on):
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
            print(f'{case.name}: {case.result}')
            if case.isPass:
                passCount+=1
            else:
                failCount+=1
        
        u.fence('total:',self.handbook['active_case_num'],'pass:',passCount,'fail:',failCount)

    def cleanDu(self):
        try:
            for proc in psutil.process_iter():
                pname = proc.name()
                if 'uesim' in pname or 'l2app' in pname:
                    proc.terminate()
        except:
            print('clean du error')
        #print('clean du')

    def cleanTrex(self,trexCnsl):
        if trexCnsl != None:
            trexCnsl.sendline('stop')
            u.sleep(self.intervalCmd)
            trexCnsl.sendline('quit')
            trexCnsl.expect(pexpect.EOF)
            trexCnsl = None
        try:
            for proc in psutil.process_iter():
                pname = proc.name()
                if '_t-rex-64' in pname:
                    proc.terminate()
        except:
            print('clean trex error')
        #print('clean trex')

    def cleanGit(self):
        repo = Repo(self.handbook['du'])
        repo.index.checkout(os.path.join(self.handbook['uesim'], 'uesimcfg.xml'), force=True)
        repo.index.checkout(os.path.join(self.handbook['nr5g'], 'cell1.xml'), force=True)
        repo.index.checkout(os.path.join(self.handbook['nr5g'], 'maccfg.xml'), force=True)
    
    def clean(self,trexCnsl):
        self.cleanDu()
        self.cleanTrex(trexCnsl)
        self.cleanGit()

    def execute(self):
        self.env()
        self.ht(self.handbook['ht'])
        console = None
        self.clean(console)
        for case in self.case_list:
            console = case.execute(console)
        self.clean(console)
        self.check()
        self.ht(True)











if __name__ == '__main__':
    octopus().execute()