import sys
import xml.etree.ElementTree as ET
import os
import shutil
from git import Repo
import pexpect
import psutil
from utils import utils as u

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
        self.group = self.handbook['case_list'][self.id]['group']

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
        self.l2Kw = (self.handbook['nr5g'],'l2.sh','stop_du.sh','cell1.xml','maccfg.xml','l2log.txt','l23_timing_stats.txt','l2app')
        self.trexKw = (self.handbook['trex'],'t-rex-64 -i','trex-console','stop','quit','flow.py','_t-rex-64')
        
        self.uesimlog = os.path.join(self.uesimKw[0],self.uesimKw[3])
        self.l2log = os.path.join(self.l2Kw[0],self.l2Kw[5])
        self.l2stats = os.path.join(self.l2Kw[0],self.l2Kw[6])

        self.uesimcfg = os.path.join(self.uesimKw[0], self.uesimKw[2])
        self.cellcfg = os.path.join(self.l2Kw[0], self.l2Kw[3])
        self.maccfg = os.path.join(self.l2Kw[0], self.l2Kw[4])

    def getInputPath(self):
        return os.path.join(self.handbook['input'],self.group,self.platform,self.name)

    def getOutputPath(self):
        injectFolder = self.algo + '_' + ('am' if self.am else 'um')
        return os.path.join(self.handbook['output'],self.group,self.platform,self.name,injectFolder,u.timestamp())

    def uesim(self):
        print('[uesim start]')
        u.execute(u.echo(u.source(self.handbook['oneapi'])),u.source(self.handbook['PATH']),u.cd(self.uesimKw[0]),u.nohup(u.echo(u.exe(self.uesimKw[1]),self.uesimKw[3])))
        u.sleep(self.intervalDu)
    
    def l2(self):
        print('[l2 start]')
        u.execute(u.echo(u.source(self.handbook['oneapi'])),u.source(self.handbook['PATH']),u.cd(self.l2Kw[0]),u.nohup(u.echo(u.exe(self.l2Kw[1]),self.l2Kw[5])))
        u.sleep(self.intervalDu)

    def du(self,on):
        if on:
            self.uesim()
            self.l2()
        else:
            print('[uesim/l2 stop]')
            u.execute(u.cd(self.l2Kw[0]),u.echo(u.exe(self.l2Kw[2])))
            u.sleep(self.intervalCmd)

    def trex(self,on):
        if self.handbook['has_trex']:
            if on:
                if self.trexCnsl is None:
                    u.execute(u.cd(self.trexKw[0]),u.nohup(u.echo(u.exe(self.trexKw[1]))))
                    u.sleep(self.intervalTrex)
                    os.chdir(self.trexKw[0])
                    self.trexCnsl = pexpect.spawn(u.exe(self.trexKw[2]))
                    u.sleep(self.intervalCmd)

                print('[trex start]')
                script = os.path.join(self.getInputPath(),self.trexKw[5])
                for para in self.trex_script_para:
                    cmd = f'start -f {script} {para}'
                    self.trexCnsl.sendline(cmd)
                    print('trex script:',cmd)
                    u.sleep(self.intervalCmd)
            else:
                self.trexCnsl.sendline(self.trexKw[3])
                u.sleep(self.intervalCmd)
                print('[trex stop]')

    def checkExist(self):
        return os.path.exists(self.uesimlog) and os.path.exists(self.l2log) and os.path.exists(self.l2stats)
    
    def checkValid(self):
        try:
            with open(self.l2stats, 'r') as file:
                for line in file:
                    if 'LV1_MAC_SCHEDULER' in line:
                        if line.count('0/0') == 3:
                            return False
                        else:
                            return True
        except:
            return False
    
    def check(self):
        isPass = self.checkExist()
        if isPass:
            isPass = self.checkValid()
        self.result = (True,'pass') if isPass else (False,'fail')

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

    def injectAlgo(self, treeL2Cell):
        idMap = {'su':'0','zfs':'1','bfs':'2','cus':'3'}

        root = treeL2Cell.getroot()
        for algo in root.iter('nMimoMode'):
            algo.text = idMap[self.algo]
        if self.algo == 'zfs':
            for sb in root.iter('nSubBand'):
                sb.text = '3'

    def injectAm(self,treeL2Cell,treeUesimcfg):
        root = treeL2Cell.getroot()
        for am in root.iter('enableRlcAm'):
            am.text = str(int(self.am))
        root = treeUesimcfg.getroot()
        for am in root.iter('enableRlcAm'):
            am.text = str(int(self.am))

    def injectIp(self,treeUesimcfg):
        root = treeUesimcfg.getroot()
        for ip in root.iter('portAddr0'):
            ip0 = ip.text
        for ip in root.iter('portAddr1'):
            ip1 = ip.text

        with open(os.path.join(self.uesimKw[0], 'dpdk.sh'), 'r+') as file:
            lines = file.readlines()
            for i,line in enumerate(lines):
                if 'ethDevice0=' in line:
                    lines[i] = 'ethDevice0=' + ip0 + '\n'
                elif 'ethDevice1=' in line:
                    lines[i] = 'ethDevice1=' + ip1 + '\n'
                    break
            file.seek(0)
            file.writelines(lines)

    def injectDsa(self,treeL2cfg):
        root = treeL2cfg.getroot()
        for dsa in root.iter('enableDSA'):
            dsa.text = str(int(self.handbook['dsa']))

    def inject(self):
        try:
            treeL2Cell = ET.parse(self.cellcfg)
            treeUesimcfg = ET.parse(self.uesimcfg)
            treeL2cfg = ET.parse(self.maccfg)

            self.injectAlgo(treeL2Cell)
            self.injectAm(treeL2Cell,treeUesimcfg)
            self.injectIp(treeUesimcfg)
            self.injectDsa(treeL2cfg)

            treeL2Cell.write(self.cellcfg)
            treeUesimcfg.write(self.uesimcfg)
            treeL2cfg.write(self.maccfg)
        except Exception as e:
            sys.exit(f'inject error:{e}')

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
        if self.trexCnsl is not None:
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
        try:
            repo = Repo(self.handbook['du'])
            repo.git.checkout(self.uesimcfg)
            repo.git.checkout(self.cellcfg)
            repo.git.checkout(self.maccfg)
        except:
            print('clean git error')
        
    def clean(self):
        self.cleanDu(True)
        self.cleanTrex()
        self.cleanGit()

    def execute(self,console):
        u.fence('case:',self.name,'id:',self.id,'total:',self.handbook['active_case_num'])
        print(' | '.join(['group: '+self.group,'algo: '+self.algo,'am: '+str(self.am)]))

        self.trexCnsl = console
        self.input()
        self.inject()
        for i in range(0,self.retry+1):
            if i > 0:
                u.fence('retry:',i,'/',self.retry)
            self.du(True)
            self.trex(True)
            print(f'duration: {self.intervalCase} second')
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

