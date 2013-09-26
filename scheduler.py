from datetime import datetime

from apscheduler.scheduler import Scheduler
import time
import logging 
logger = logging.getLogger(__name__)

# Start the scheduler
sched = Scheduler()
sched.start()

def job_function(dht_obj):
    logger.info(dht_obj.reg.node_id)
    

# Schedule job_function to be called every two hours
def bind_jobs(dht_obj):
    sched.add_interval_job(job_function, seconds=60,args=[dht_obj])
#    sched.add_interval_job(job_function, hours=2, start_date='2010-10-10 09:30',[dht_obj])
