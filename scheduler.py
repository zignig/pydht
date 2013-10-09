from datetime import datetime

from apscheduler.scheduler import Scheduler
import time
import logging 
logger = logging.getLogger(__name__)

# Start the scheduler
sched = Scheduler()
sched.start()

def job_function(dht_obj):
    re_rep = dht_obj.reg.doc_store.replicate()


    

# Schedule job_function to be called every two hours
def bind_jobs(dht_obj):
    sched.add_interval_job(job_function, seconds=10,args=[dht_obj])
#    sched.add_interval_job(job_function, hours=2, start_date='2010-10-10 09:30',[dht_obj])
