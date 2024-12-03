import shutil
from flask import Flask, render_template, request, send_file
import os
from apscheduler.schedulers.background import BackgroundScheduler
from octopus import octopus
from handbook import handbook
from utils import utils as u
from git import Repo

app = Flask(__name__)
handbook = handbook().get()

LOG_DIR = handbook['output']
print('log from:',LOG_DIR)

def get_log_files(path):
    log_files = []
    for entry in os.scandir(path):
        log_files.append({
            'name': entry.name,
            'path': os.path.relpath(entry.path, LOG_DIR),
            'is_dir': entry.is_dir(),
        })
    log_files.sort(key=lambda x: x['name'], reverse=True)
    return log_files

@app.route('/')
def index():
    path = request.args.get('path', '')
    full_path = os.path.join(LOG_DIR, path)
    root_exists = os.path.exists(full_path)
    log_files = get_log_files(full_path) if root_exists else []
    parent_path = os.path.dirname(path) if path else None
    return render_template('index.html', log_files=log_files, parent_path=parent_path, root_exists=root_exists)

@app.route('/log/<path:log_path>')
def show_log(log_path):
    full_path = os.path.join(LOG_DIR, log_path)
    try:
        with open(full_path, 'r') as file:
            log_content = file.read()
    except FileNotFoundError:
        log_content = "Log file not found."
    log_name = os.path.basename(log_path)
    parent_path = os.path.dirname(log_path)
    return render_template('log.html', log_name=log_name, log_content=log_content, parent_path=parent_path)

@app.route('/download_log/<path:log_path>')
def download_log(log_path):
    full_path = os.path.join(LOG_DIR, log_path)
    try:
        return send_file(full_path, as_attachment=True)
    except FileNotFoundError:
        return "Log file not found.", 404
    
def update_git():
    repo = Repo(handbook['du'])
    # repo.git.checkout('.')
    repo.remotes.origin.pull()

def update_bin_uesim():
    make = os.path.join(handbook['uesim'],'make')
    try:
        shutil.rmtree(make)
    except Exception:
        print(f'remove {make} fail')

    u.execute(u.echo(u.source(handbook['oneapi'])),u.source(handbook['PATH']),u.cd(handbook['uesim']),u.nohup(u.echo(u.exe('build_uesim.sh'),'run.log')))

def update_bin_l2():
    make = os.path.join(handbook['nr5g'],'make')
    try:
        shutil.rmtree(make)
    except Exception:
        print(f'remove {make} fail')

    u.execute(u.echo(u.source(handbook['oneapi'])),u.source(handbook['PATH']),u.cd(handbook['nr5g']),u.nohup(u.echo(u.exe('build_mac.sh'),'run.log')))

def update_log():
    octopus().execute()

def clean_log():
    try:
        shutil.rmtree(LOG_DIR)
    except Exception:
        print(f'remove {LOG_DIR} fail')

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_git,'cron',hour=0,minute=0)
    scheduler.add_job(update_bin_uesim,'cron',hour=0,minute=1)
    scheduler.add_job(update_bin_l2,'cron',hour=0,minute=2)
    scheduler.add_job(update_log,'cron',hour=0,minute=3)
    scheduler.add_job(clean_log, 'cron', day=1, hour=23, minute=0)
    scheduler.start()
    try:
        app.run(host='0.0.0.0',port=8100)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()