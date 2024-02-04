import subprocess
import time

class util:
    def cd(path):
        return 'cd ' + path
    
    def source(path):
        return 'source ' + path
    
    def execute(*args):
        cmd = ''
        for i in range(len(args)):
            if i==0:
                cmd += args[i]
            else:
                cmd += ';'+args[i]
        #print(cmd)
        subprocess.Popen(['bash', '-c', f'{cmd}'])

    def sleep(interval):
        time.sleep(interval)

    def timestamp():
        return time.strftime("%Y%m%d%H%M%S", time.localtime())
    
    def fence(*args):
        left = '###############'
        right = '################################################'
        info = left
        total = 30
        cost = 0
        for i in args:
            info += ' '
            cost += len(' ')
            if type(i) != str:
                info += str(i)
                cost += len(str(i))
            else:
                info += i
                cost += len(i)
        rest = total - cost
        for i in range(0,rest):
            info += ' '
        info += right
        print(info)


