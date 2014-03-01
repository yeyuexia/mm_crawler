import os.path
import time
import urllib2
import urlparse
import Queue
import threading
import logging
from functools import wraps

from bs4 import BeautifulSoup

LOG_FORMAT = "%(asctime)-15s -- %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger("crawler")

def info_log(message):
    logger.info(message)

def error_log(message):
    logger.error(message)

def lock(func):
    """a decorate for Master"""
    @wraps(func)
    def decorate(obj, *args, **kw):
        with obj._task_lock:
            ret = func(obj, *args, **kw)
        return ret
    return decorate

class Master(object):
    """the cawler master used for task assignment.
    task is a tuple format likes (type, url)
    TODO: we need use database instead set() to store scan url, otherwise the program would crashed when scan too many urls,
    use different locks for each {scan} and {number}
    and the class implemention should be changed?
    """
    TASK_TYPE_IMAGE = 0
    TASK_TYPE_URL = 1

    _lock = threading.Lock()
    _task_lock = threading.Lock()
    _instance = None
    def __init__(self):
        self.queue = Queue.Queue()
        self.scan = set()
        self.number = 0
        self.capicity = -1
        info_log("Master init")

    @classmethod
    def instance(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = Master()
        return cls._instance

    @classmethod
    def set_capicity(cls, capicity):
        cls.instance().capicity = capicity
        info_log("set crawler capicity:%d"%capicity)

    @classmethod
    def get_task(cls):
        try:
            task = cls.instance().queue.get(block=False)
        except Exception as e:
            task = None
        return task

    @classmethod
    @lock
    def push_task(cls, task):
        if task[1] not in cls.instance().scan:
            cls.instance().scan.add(task[1])
            cls.instance().queue.put(task)
            info_log("push_task %s"%str(task))

    @classmethod
    @lock
    def finish_task(cls, task):
        if task[0] == cls.TASK_TYPE_IMAGE:
            if cls.instance().number < cls.instance().capicity:
                cls.instance().number += 1
            info_log("task %s finished, complete number:%d"%(str(task), cls.instance().number))
        else:
            info_log("task %s finished"%str(task))

    @classmethod
    def finished(cls):
        """check does mission finished"""
        if cls.instance().capicity < 0: #if capicity < 0, 
            return False
        ret = False
        with cls._task_lock:
            ret = cls.instance().capicity <= cls.instance().number
        return ret

class Worker(threading.Thread):
    """download res by url and parser"""
    def __init__(self, worker_number, output_path, sleep_time=5, retry_times=5, max_sleep_times=10):
        threading.Thread.__init__(self)
        self.worker_number = worker_number
        self.daemon = True
        self.error_count = 0
        self.retry_times = retry_times
        self.max_sleep_times = max_sleep_times
        self.sleep_time = sleep_time
        self.sleep_count = 0
        self.output_path = output_path
        info_log("Worker init number:%d"%worker_number)

    def _gen_url(self, host, url):
        if url.startswith("/"):
            url = host + url
        return url.strip()

    def _is_vaild_resource(self, url):
        """simple check is vaild image resource
        TODO: we can rewrite this method to get more effective result
        """
        if self._is_vaild_url(url) and url.endswith(".jpg") and url.find("meimei22.com/") != -1 and url.find("pic") != -1:
            return True
        return False

    def _is_vaild_url(self, url):
        """ simple check is a vaild url
        TODO: we can rewrite this method to get more effective result
        """
        return True if url.startswith("http://") else False

    def _parser_html(self, url, html):
        """parser html and get the needed resources"""
        soup = BeautifulSoup(html)
        tasks, image_links, href_links = [], [], []
        for img_tag in soup.find_all("img"):
            link = img_tag.get("src")
            if link:
                link = self._gen_url(url, link)
            image_links.append(link)
        tasks.extend([(Master.TASK_TYPE_IMAGE, link) for link in image_links if self._is_vaild_resource(link)])
        for href_tag in soup.find_all("a"):
            link = href_tag.get("href")
            if link:
                link = self._gen_url(url, link)
                href_links.append(link)
        tasks.extend([(Master.TASK_TYPE_URL, link) for link in href_links if self._is_vaild_url(link)])
        return tasks

    def run(self):
        while True:
            try:
                if Master.finished():
                    break
                task = Master.get_task()
                if not task:
                    time.sleep(self.sleep_time)
                    self.sleep_count += 1
                    if self.sleep_count >= self.max_sleep_times:
                        break
                    continue
                task_type, url = task
                res = urllib2.urlopen(url).read()
                if task_type == Master.TASK_TYPE_IMAGE:
                    output_file = os.path.join(self.output_path, url.replace("/", ""))
                    if Master.finished(): break
                    open(output_file, "wb").write(res)
                elif task_type == Master.TASK_TYPE_URL:
                    parser = urlparse.urlparse(url)
                    base_url = parser.scheme + "://" + parser.netloc
                    tasks = self._parser_html(base_url, res)
                    if Master.finished(): break
                    map(lambda task: Master.push_task(task), tasks)
                Master.finish_task(task)
                self.sleep_count = 0
            except Exception as e:
                import traceback
                error_log("worker %d error: %s\n%s"%(self.worker_number, e, traceback.format_exc()))
                if self.error_count > self.retry_times:
                    break
                else:
                    continue
        info_log("worker %d stop"%self.worker_number)

def run(begin_url, capicity, output_path, thread_num):
    Master.set_capicity(capicity)
    Master.push_task((Master.TASK_TYPE_URL, begin_url))
    workers = map(lambda num: Worker(num, output_path), range(1, 1+thread_num))
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    info_log("crawler finished")
