import subprocess
import time

class util:
    def cd(path):
        return 'cd ' + path
    
    def source(path):
        return 'source ' + path
    
    def execute(*args):
        subprocess.Popen(['bash','-c',';'.join(args)])

    def sleep(interval):
        time.sleep(interval)

    def timestamp():
        return time.strftime('%Y%m%d%H%M%S', time.localtime())
    
    def fence(*args):
        print((' '.join([str(i) for i in args])).center(90,'#'))
