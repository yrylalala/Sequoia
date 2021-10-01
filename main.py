# -*- encoding: UTF-8 -*-

import utils
import logging
import work_flow
import settings
import schedule
import time
import datetime
import os
import shutil


def job():
    if utils.is_weekday():
        work_flow.process()


# 指定输入位置
log_file_path = './' + datetime.date.today().strftime('%m%d')
if not os.path.exists(log_file_path):
    os.makedirs(log_file_path)
else:
    shutil.rmtree(log_file_path)
    os.makedirs(log_file_path)

if os.path.exists('./data'):
    shutil.rmtree('./data')

logging.basicConfig(format='%(asctime)s %(message)s', filename=log_file_path + '/sequoia.log', filemode='w')
logging.getLogger().setLevel(logging.INFO)
settings.init()

if settings.config['cron']:
    EXEC_TIME = "15:15"
    schedule.every().day.at(EXEC_TIME).do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    work_flow.process()
    work_flow.statistical_result()
