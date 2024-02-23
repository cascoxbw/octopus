import xml.etree.ElementTree as ET
import os
import shutil
from git import Repo
import pexpect
import psutil
from util import util as u

class case:
    def __init__(self,id,handbook):
        self.handbook = handbook
        self.initProp(id)
        self.initCtrl()
        self.initKw()

    def initProp(self,id):
        self.platform = self.handbook['platform']
        self.id = id
        self.name = self.handbook['case_list'][self.id]['name']
        self.trex_script_para = self.handbook['case_list'][self.id]['trex_script_para']
        self.algo = self.handbook['case_list'][self.id]['algo']
        if self.handbook['is_global_algo']:
            self.algo = self.handbook['global_algo']
    
    def initCtrl(self):
        self.intervalDu = 15
        self.intervalTrex = 30
        self.intervalCmd = 5
        self.intervalCase = 30
        self.retry = self.handbook['retry']
        self.result = (False,'fail')
        self.trexCnsl = None

    def initKw(self):
        self.uesimKw = (self.handbook['uesim'],'./uesim.sh','uesimcfg.xml','uesimlog.txt','uesim')
        self.l2Kw = (self.handbook['nr5g'],'./l2.sh','./stopdu.sh','cell1.xml','maccfg.xml','l2log.txt','l23_timing_stats.txt','l2app')
        self.trexKw = (self.handbook['trex'],'./t-rex-64 -i','./trex-console','stop','quit','flow.py','_t-rex-64')

    def getInputPath(self):
        return os.path.join(self.handbook['input'],self.platform,self.name)

    def getOutputPath(self):
        return os.path.join(self.handbook['output'],self.platform,self.name,self.algo,u.timestamp())

    def uesim(self):
        print('[uesim start]')
        cd = u.cd(self.uesimKw[0])
        cmd = f'nohup {self.uesimKw[1]} > {self.uesimKw[3]} 2>&1 &'
        u.execute(cd,cmd)
    
    def l2(self):
        print('[l2 start]')
        cd = u.cd(self.l2Kw[0])
        cmd = f'nohup {self.l2Kw[1]} > {self.l2Kw[5]} 2>&1 &'
        u.execute(cd,cmd)

    def du(self,on):
        if on:
            self.uesim()
            u.sleep(self.intervalDu)
            self.l2()
            u.sleep(self.intervalDu)
        else:
            print('[du stop]')
            cd = u.cd(self.l2Kw[0])
            cmd = f'{self.l2Kw[2]} &> /dev/null'
            u.execute(cd,cmd)

    def trex(self,on):
        if on:
            if self.trexCnsl is None:
                os.chdir(self.trexKw[0])
                os.system(f'{self.trexKw[1]} > null.log 2>&1 &')
                u.sleep(self.intervalTrex)
                self.trexCnsl = pexpect.spawn(self.trexKw[2])
                u.sleep(self.intervalCmd)

            script = os.path.join(self.getInputPath(),self.trexKw[5])
            for para in self.trex_script_para:
                cmd = f'start -f {script} {para}'
                self.trexCnsl.sendline(cmd)
                print('trex para:',cmd)
                u.sleep(self.intervalCmd)
            print('[trex start]')
        else:
            self.trexCnsl.sendline(self.trexKw[3])
            u.sleep(self.intervalCmd)
            print('[trex stop]')

    def check(self):
        cond = os.path.exists(os.path.join(self.uesimKw[0],self.uesimKw[3]))\
               and os.path.exists(os.path.join(self.l2Kw[0],self.l2Kw[5]))\
               and os.path.exists(os.path.join(self.l2Kw[0],self.l2Kw[6]))
        self.result = (True,'pass') if cond else (False,'fail')

    def output(self):
        dst = self.getOutputPath()
        print('output to:', dst)
        try:
            os.makedirs(dst)
            shutil.move(os.path.join(self.uesimKw[0],self.uesimKw[3]), dst)
            shutil.move(os.path.join(self.l2Kw[0],self.l2Kw[5]), dst)
            shutil.move(os.path.join(self.l2Kw[0],self.l2Kw[6]), dst)
        except:
            print('output error')

    def injectAlgo(self):
        idMap = {'su':'0','zfs':'1','bfs':'2','cus':'3'}
        subbandMap = {'su':'1','zfs':'3','bfs':'1','cus':'1'}
        dst = os.path.join(self.l2Kw[0],self.l2Kw[3])
        try:
            tree = ET.parse(dst)
            root = tree.getroot()
            for algo in root.iter('nMimoMode'):
                algo.text = idMap[self.algo]
            for sb in root.iter('nSubBand'):
                sb.text = subbandMap[self.algo]
            tree.write(dst)
        except Exception as e:
            print('inject algo error:',e)
    
    def inject(self):
        self.injectAlgo()

    def input(self):
        src = self.getInputPath()
        print('input from:', src)
        try:
            shutil.copy2(os.path.join(src, self.uesimKw[2]), self.uesimKw[0])
            shutil.copy2(os.path.join(src, self.l2Kw[3]), self.l2Kw[0])
            shutil.copy2(os.path.join(src, self.l2Kw[4]), self.l2Kw[0])
        except:
            print('input error')

    def cleanDu(self):
        try:
            for proc in psutil.process_iter():
                pname = proc.name()
                if self.uesimKw[-1] in pname or self.l2Kw[-1] in pname:
                    proc.terminate()
        except:
            print('clean du error')
        #print('clean du')
    
    def cleanTrex(self):
        if self.trexCnsl != None:
            self.trexCnsl.sendline(self.trexKw[3])
            u.sleep(self.intervalCmd)
            self.trexCnsl.sendline(self.trexKw[4])
            self.trexCnsl.expect(pexpect.EOF)
            self.trexCnsl = None
        try:
            for proc in psutil.process_iter():
                pname = proc.name()
                if self.trexKw[-1] in pname:
                    proc.terminate()
        except:
            print('clean trex error')
        #print('clean trex')

    def cleanGit(self):
        repo = Repo(self.handbook['du'])
        repo.index.checkout(os.path.join(self.uesimKw[0], self.uesimKw[2]), force=True)
        repo.index.checkout(os.path.join(self.l2Kw[0], self.l2Kw[3]), force=True)
        repo.index.checkout(os.path.join(self.l2Kw[0], self.l2Kw[4]), force=True)
    
    def clean(self):
        self.cleanDu()
        self.cleanTrex()
        self.cleanGit()

    def execute(self,console):
        u.fence('case:',self.name,'id:',self.id,'total:',self.handbook['active_case_num'])
        print('algo:',self.algo)

        self.trexCnsl = console
        self.input()
        self.inject()
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
            if self.result[0]:
                self.output()
                break

        u.fence('case:',self.name,'result:',self.result[1])
        return self.trexCnsl

