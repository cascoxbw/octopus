import xml.etree.ElementTree as ET
import os
import shutil
from git import Repo
import pexpect
import psutil
from util import util as u

class tentacle:
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
        self.am = self.handbook['case_list'][self.id]['am']
        if self.handbook['is_global']:
            self.algo = self.handbook['global_algo']
            self.am = self.handbook['global_am']

    def initCtrl(self):
        self.intervalDu = 15
        self.intervalTrex = 30
        self.intervalCmd = 5
        self.intervalCase = self.handbook['duration']
        self.retry = self.handbook['retry']
        self.result = (False,'fail')
        self.trexCnsl = None

    def initKw(self):
        self.uesimKw = (self.handbook['uesim'],'uesim.sh','uesimcfg.xml','uesimlog.txt','uesim')
        self.l2Kw = (self.handbook['nr5g'],'l2.sh','stopdu.sh','cell1.xml','maccfg.xml','l2log.txt','l23_timing_stats.txt','l2app')
        self.trexKw = (self.handbook['trex'],'t-rex-64','trex-console','stop','quit','flow.py','_t-rex-64')
        
        self.uesimlog = os.path.join(self.uesimKw[0],self.uesimKw[3])
        self.l2log = os.path.join(self.l2Kw[0],self.l2Kw[5])
        self.l2stats = os.path.join(self.l2Kw[0],self.l2Kw[6])

        self.uesimcfg = os.path.join(self.uesimKw[0], self.uesimKw[2])
        self.l2cell = os.path.join(self.l2Kw[0], self.l2Kw[3])
        self.l2cfg = os.path.join(self.l2Kw[0], self.l2Kw[4])

    def getInputPath(self):
        return os.path.join(self.handbook['input'],self.platform,self.name)

    def getOutputPath(self):
        injectFolder = self.algo + '_' + ('am' if self.am else 'um')
        return os.path.join(self.handbook['output'],self.platform,self.name,injectFolder,u.timestamp())

    def uesim(self):
        print('[uesim start]')
        u.execute(u.cd(self.uesimKw[0]),f'nohup ./{self.uesimKw[1]} > {self.uesimKw[3]} 2>&1 &')
    
    def l2(self):
        print('[l2 start]')
        u.execute(u.cd(self.l2Kw[0]),f'nohup ./{self.l2Kw[1]} > {self.l2Kw[5]} 2>&1 &')

    def du(self,on):
        if on:
            self.uesim()
            u.sleep(self.intervalDu)
            self.l2()
            u.sleep(self.intervalDu)
        else:
            print('[du stop]')
            u.execute(u.cd(self.l2Kw[0]),f'./{self.l2Kw[2]} &> /dev/null')

    def trex(self,on):
        if on:
            if self.trexCnsl is None:
                u.execute(u.cd(self.trexKw[0]),f'nohup ./{self.trexKw[1]} -i &> /dev/null')
                u.sleep(self.intervalTrex)
                os.chdir(self.trexKw[0])
                self.trexCnsl = pexpect.spawn(f'./{self.trexKw[2]}')
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
        cond = os.path.exists(self.uesimlog) and os.path.exists(self.l2log) and os.path.exists(self.l2stats)
        self.result = (True,'pass') if cond else (False,'fail')

    def output(self):
        dst = self.getOutputPath()
        print('output to:', dst)
        try:
            os.makedirs(dst)
            shutil.move(self.uesimlog, dst)
            shutil.move(self.l2log, dst)
            shutil.move(self.l2stats, dst)
        except:
            print('output error')

    def injectAlgo(self):
        idMap = {'su':'0','zfs':'1','bfs':'2','cus':'3'}
        # subbandMap = {'su':'1','zfs':'3','bfs':'1','cus':'1'}
        try:
            tree = ET.parse(self.l2cell)
            root = tree.getroot()
            for algo in root.iter('nMimoMode'):
                algo.text = idMap[self.algo]
            # for sb in root.iter('nSubBand'):
            #     sb.text = subbandMap[self.algo]
            tree.write(self.l2cell)
        except Exception as e:
            print('inject algo error:',e)
    
    def injectAm(self):
        try:
            tree = ET.parse(self.l2cell)
            root = tree.getroot()
            for am in root.iter('enableRlcAm'):
                am.text = str(int(self.am))
            tree.write(self.l2cell)

            tree = ET.parse(self.uesimcfg)
            root = tree.getroot()
            for am in root.iter('enableRlcAm'):
                am.text = str(int(self.am))
            tree.write(self.uesimcfg)
        except Exception as e:
            print('inject am error:',e)

    def inject(self):
        self.injectAlgo()
        self.injectAm()

    def input(self):
        src = self.getInputPath()
        print('input from:', src)
        try:
            shutil.copy2(os.path.join(src, self.uesimKw[2]), self.uesimKw[0])
            shutil.copy2(os.path.join(src, self.l2Kw[3]), self.l2Kw[0])
            shutil.copy2(os.path.join(src, self.l2Kw[4]), self.l2Kw[0])
        except:
            print('input error')

    def cleanDu(self,rm):
        try:
            if rm:
                rms = (self.uesimlog,self.l2log,self.l2stats)
                for i in rms:
                    if os.path.exists(i):
                        os.remove(i)
        
            for proc in psutil.process_iter():
                pname = proc.name()
                if self.uesimKw[-1] in pname or self.l2Kw[-1] in pname:
                    proc.terminate()
        except:
            print('clean du error')
    
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

    def cleanGit(self):
        repo = Repo(self.handbook['du'])
        repo.index.checkout(self.uesimcfg, force=True)
        repo.index.checkout(self.l2cell, force=True)
        repo.index.checkout(self.l2cfg, force=True)
    
    def clean(self):
        self.cleanDu(True)
        self.cleanTrex()
        self.cleanGit()

    def execute(self,console):
        u.fence('case:',self.name,'id:',self.id,'total:',self.handbook['active_case_num'])
        print('algo:',self.algo)
        print('am:',self.am)

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
            self.cleanDu(False)
            if self.result[0]:
                self.output()
                break

        u.fence('case:',self.name,'result:',self.result[1])
        return self.trexCnsl

