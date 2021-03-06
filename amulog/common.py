#!/usr/bin/env python
# coding: utf-8

import os
import time
import datetime
import logging
import subprocess  # for python3
#import subprocess32 as subprocess  # for python2
from collections import UserDict  # for python3
#from UserDict import UserDict  # for python2


# args
json_args = {"ensure_ascii" : False,
             "indent" : 4,
             "sort_keys" : True}


# classes

class singleton(object):

    def __new__(clsObj, *args, **kwargs):
        tmpInstance = None
        if not hasattr(clsObj, "_instanceDict"):
            clsObj._instanceDict = {}
            clsObj._instanceDict[str(hash(clsObj))] = \
                    super(singleton, clsObj).__new__(clsObj, *args, **kwargs)
            tmpInstance = clsObj._instanceDict[str(hash(clsObj))]
        elif not hasattr(clsObj._instanceDict, str(hash(clsObj))):
            clsObj._instanceDict[str(hash(clsObj))] = \
                    super(singleton, clsObj).__new__(clsObj, *args, **kwargs)
            tmpInstance = clsObj._instanceDict[str(hash(clsObj))]
        else:
            tmpInstance = clsObj._instanceDict[str(hash(clsObj))]
        return tmpInstance


class IDDict():

    def __init__(self, keyfunc = None):
        self._d_obj = {}
        self._d_id = {}
        if keyfunc is None:
            self.keyfunc = lambda x: x
        else:
            self.keyfunc = keyfunc

    def _next_id(self):
        next_id = len(self._d_obj)
        assert not next_id in self._d_obj
        return next_id

    def add(self, obj):
        if self.exists(obj):
            return self._d_id[self.keyfunc(obj)]
        else:
            keyid = self._next_id()
            self._d_obj[keyid] = obj
            self._d_id[self.keyfunc(obj)] = keyid
            return keyid

    def exists(self, obj):
        return self.keyfunc(obj) in self._d_id

    def get(self, keyid):
        return self._d_obj[keyid]


# file managing

def is_empty(dirname):
    if os.path.isdir(dirname):
        if len(os.listdir(dirname)) > 1:
            return True
        else:
            return False
    else:
        return False


def rep_dir(args):
    if isinstance(args, list):
        ret = []
        for arg in args:
            if os.path.isdir(arg):
                ret.extend(["/".join((arg, fn)) \
                        for fn in sorted(os.listdir(arg))])
            else:
                ret.append(arg)
        return ret
    elif isinstance(args, str):
        arg = args
        if os.path.isdir(arg):
            return ["/".join((arg, fn)) for fn in sorted(os.listdir(arg))]
        else:
            return [arg]
    else:
        raise NotImplementedError


def recur_dir(args):

    def open_path(path):
        if os.path.isdir(path):
            ret = []
            for fn in sorted(os.listdir(path)):
                ret += open_path("/".join((path, fn)))
            return ret
        else:
            return [path]

    if isinstance(args, list):
        l_fn = []
        for arg in args:
            l_fn += open_path(arg)
    elif isinstance(args, str):
        l_fn = open_path(args)
    else:
        raise NotImplementedError
    return l_fn


def filepath(dn, fn):
    if len(dn) == 0:
        return fn
    else:
        return "/".join((dn, fn))


def filename(fp):
    if "/" in fp:
        return fp.split("/")[-1]
    else:
        return fp


def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    elif not os.path.isdir(path):
        raise OSError("something already exists on given path, " \
                "and it is NOT a directory")
    else:
        pass


def rm(path):
    if os.path.exists(path):
        os.remove(path)
        return True
    else:
        return False


def rm_dirchild(dirpath):
    for fpath in rep_dir(dirpath):
        os.remove(fpath)


def last_modified(args, latest = False):
    """Get the last modified time of a file or a set of files.

    Args:
        args (str or list[str]): Files to investigate.
        latest (Optional[bool]): If true, return the latest datetime
                of timestamps. Otherwise, return the oldest timestamp.

    Returns:
        datetime.datetime

    """
    def file_timestamp(fn):
        stat = os.stat(fn)
        t = stat.st_mtime
        return datetime.datetime.fromtimestamp(t)

    if isinstance(args, list):
        l_dt = [file_timestamp(fn) for fn in args]
        if latest:
            return max(l_dt)
        else:
            return min(l_dt)
    elif isinstance(args, str):
        return file_timestamp(args)
    else:
        raise NotImplementedError


# subprocess
def call_process(cmd):
    """Call a subprocess and handle standard outputs.
    
    Args:
        cmd (list): A sequence of command strings.
    
    Returns:
        ret (int): Return code of the subprocess.
        stdout (str)
        stderr (str)
    """

    p = subprocess.Popen(cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    ret = p.returncode
    return ret, stdout, stderr


# parallel computing

def mprocess(l_process, pal):
    """
    Handle multiprocessing with an upper limit of working processes.
    This function incrementally fill working processes with remaining tasks.
    This function does not use memory sharing or process communications.
    If you need processe communications,
    use common.mprocess_queueing.

    Args:
        l_process (List(multiprocess.Process))
        pal (int): Maximum number of processes executed at once.
    """

    l_job = []
    while len(l_process) > 0:
        if len(l_job) < pal:
            job = l_process.pop(0)
            job.start()
            l_job.append(job)
        else:
            time.sleep(1)
            l_job = [j for j in l_job if j.is_alive()]
    else:
        for job in l_job:
            job.join()


def mprocess_queueing(l_pq, pal):
    """
    Same as mprocess, but this function yields
    returned values of every processes with multiprocessing.Queue.

    Args:
        l_pq (List[multiprocessing.Process, multiprocessingQueue])
        pal (int): Maximum number of processes executed at once.
    """

    l_job = []
    while len(l_pq) > 0:
        if len(l_job) < pal:
            process, queue = l_pq.pop(0)
            process.start()
            l_job.append((process, queue))
        else:
            time.sleep(1)
            l_temp = []
            for process, queue in l_job:
                if queue.empty():
                    l_temp.append((process, queue))
                else:
                    ret = queue.get()
                    yield ret
                    assert queue.empty()
                    process.join()
                    queue.close()
            l_job = l_temp
    else:
        while len(l_job) > 0:
            time.sleep(1)
            l_temp = []
            for process, queue in l_job:
                if queue.empty():
                    l_temp.append((process, queue))
                else:
                    ret = queue.get()
                    yield ret
                    assert queue.empty()
                    process.join()
                    queue.close()
            l_job = l_temp


#def mthread_queueing(l_thread, pal):
#    """
#    Args:
#        l_thread (List[threading.Thread]): A sequence of thread objects.
#        pal (int): Maximum number of threads executed at once.
#    """
#    l_job = []
#    while len(l_thread) > 0:
#        if len(l_job) < pal:
#            job = l_thread.pop(0)
#            job.start()
#            l_job.append(job)
#        else:
#            time.sleep(1)
#            l_job = [j for j in l_job if j.is_alive()]
#    else:
#        for job in l_job:
#            job.join()
#
#
#def mprocess_queueing(l_process, pal):
#    mthread_queueing(l_process, pal)


# measurement

class Timer():

    def __init__(self, header, output = None):
        self.start_dt = None
        self.header = header
        self.output = output

    def _output(self, string):
        if isinstance(self.output, logging.Logger):
            self.output.info(string)
        else:
            print(string)

    def start(self):
        self.start_dt = datetime.datetime.now()
        self._output("{0} start".format(self.header))

    def stop(self):
        if self.start_dt is None:
            raise AssertionError("call start() before stop()")
        self.end_dt = datetime.datetime.now()
        self._output("{0} done ({1})".format(self.header,
                self.end_dt - self.start_dt))


# visualization

def cli_table(table, spl = " ", fill = " ", align = "left"):
    """
    Args:
        table (List[List[str]]): input data
        spl (str): splitting string of columns
        fill (str): string of 1 byte, used to fill the space
        align (str): left and right is available
    """
    len_row = len(table)
    len_column = len(table[0])
    col_max = [0] * len_column

    for row in table:
        for cid, val in enumerate(row):
            if cid >= len_column:
                raise ValueError
            val = str(val)
            if len(val) > col_max[cid]:
                col_max[cid] = len(val)

    l_buf = []
    for row in table:
        line = []
        for cid, val in enumerate(row):
            cell = str(val)
            len_cell = col_max[cid]
            len_space = len_cell - len(cell)
            if align == "left":
                cell = cell + fill * len_space
            elif align == "right":
                cell = fill * len_space + cell
            else:
                raise NotImplementedError
            line.append(cell)
        l_buf.append(spl.join(line))

    return "\n".join(l_buf)


# compatibility

def pickle_comp_args(comp):
    if comp:
        d = {"encoding": "bytes"}
    else:
        d = {}
    return d


