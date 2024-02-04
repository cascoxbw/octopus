import os
import shutil
import pexpect
import psutil
from util import util as u

class case:
    def __init__(self,id,config,platform):
        self.id = id
        self.handbook = config
        self.platform = platform

        self.name = self.handbook['case_list'][self.id]['name']
        self.trex_script_para = self.handbook['case_list'][self.id]['trex_script_para']

        self.intervalDu = 15
        self.intervalTrex = 30
        self.intervalCmd = 5
        self.intervalCase = 30
        self.retry = 1
        self.result = 'fail'
        self.isPass = False
        self.trexCnsl = None

        self.uesimLog = 'uesimlog.txt'
        self.l2Log = 'l2log.txt'
        self.l2stats = 'l23_timing_stats.txt'
        self.uesimPath = self.handbook['uesim']
        self.l2Path = self.handbook['nr5g']
        self.trexPath = self.handbook['trex']

    def uesim(self):
        print("uesim start")
        uesim = u.cd(self.uesimPath)
        uesim1 = f"nohup ./uesim.sh > {self.uesimLog} 2>&1 &"
        u.execute(uesim,uesim1)
    
    def l2(self):
        print("l2 start")
        l2 = u.cd(self.l2Path)
        l21 = f"nohup ./l2.sh > {self.l2Log} 2>&1 &"
        u.execute(l2,l21)

    def du(self,on):
        if on:
            self.uesim()
            u.sleep(self.intervalDu)
            self.l2()
            u.sleep(self.intervalDu)
        else:
            print("du stop")
            l2 = u.cd(self.l2Path)
            cmd = "./stopdu.sh &> /dev/null"
            u.execute(l2,cmd)

    def trex(self,on):
        if on:
            if self.trexCnsl is None:
                os.chdir(self.trexPath)
                os.system("./t-rex-64 -i > server.log 2>&1 &")
                u.sleep(self.intervalTrex)
                os.chdir(self.trexPath)
                self.trexCnsl = pexpect.spawn("./trex-console")
                u.sleep(self.intervalCmd)

            path = self.handbook['input'] + self.name + '/' + self.platform + '/'
            for para in self.trex_script_para:
                self.trexCnsl.sendline(f"start -f {path}flow.py {para}")
                print(f"start -f {path}flow.py {para}")
                u.sleep(self.intervalCmd)
            print("trex start")
        else:
            self.trexCnsl.sendline('stop')
            u.sleep(self.intervalCmd)
            print("trex stop")

    def check(self):
        if os.path.exists(self.uesimPath + self.uesimLog)\
            and os.path.exists(self.l2Path + self.l2Log)\
              and os.path.exists(self.l2Path + self.l2stats):
            self.isPass = True
            self.result = 'pass'
        else:
            self.isPass = False
            self.result = 'fail'

    def output(self):
        path = self.handbook['output'] + self.name + "_" + u.timestamp()
        print("output to: ", path)
        try:
            os.makedirs(path)
            shutil.move(f"{self.uesimPath+self.uesimLog}", path)
            shutil.move(f"{self.l2Path+self.l2Log}", path)
            shutil.move(f"{self.l2Path+self.l2stats}", path)
        except:
            print("output error")

    def input(self):
        path = self.handbook['input'] + self.name + '/' + self.platform + '/'
        print("input from: ", path)
        try:
            shutil.copy2(os.path.join(path, "uesimcfg.xml"), self.uesimPath)
            shutil.copy2(os.path.join(path, "cell1.xml"), self.l2Path)
            shutil.copy2(os.path.join(path, "maccfg.xml"), self.l2Path)
        except:
            print("input error")

    def cleanDu(self):
        try:
            for proc in psutil.process_iter():
                pname = proc.name()
                if 'uesim' in pname or 'l2app' in pname:
                    proc.terminate()
        except:
            print('clean du error')
        #print('clean du')

    def cleanTrex(self):
        if self.trexCnsl != None:
            self.trexCnsl.sendline('stop')
            u.sleep(self.intervalCmd)
            self.trexCnsl.sendline('quit')
            self.trexCnsl.expect(pexpect.EOF)
            self.trexCnsl = None
        try:
            for proc in psutil.process_iter():
                pname = proc.name()
                if '_t-rex-64' in pname:
                    proc.terminate()
        except:
            print('clean trex error')
        #print('clean trex')

    def clean(self):
        self.cleanDu()
        self.cleanTrex()

    def execute(self,console):
        u.fence('case:',self.name,'id:',self.id,'total:',self.handbook['case_num'])
        self.trexCnsl = console
        self.input()
        for i in range(0,self.retry+1):
            if i > 0:
                u.fence('retry:',i,'/',self.retry)
            self.du(True)
            self.trex(True)
            u.sleep(self.intervalCase)
            self.du(False)
            self.trex(False)
            self.check()
            self.cleanDu()
            if self.isPass:
                self.output()
                break
        #self.cleanTrex()
        u.fence('case:',self.name,'result:',self.result)
        return self.trexCnsl

