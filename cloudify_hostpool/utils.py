
from lockfile import LockFile
from cloudify_hostpool import exceptions
from flask import request
import os

HOST_POOL_LOG_FILE='HOST_POOL_LOG_FILE'

def write_to_log(caller_string, message_text, log_file=None):
    try:
        if log_file is None:
            log_file = get_log_filename()
        lock = LockFile(log_file)
        lock.acquire()
        current_message = "{0}: {1}\n".format(caller_string, message_text)
        with open(log_file, 'a') as f:
            f.write(current_message)
            f.close()
    except:
        err_message = "{0}: Failures while locking or using {1}".format(caller_string, log_file)
        lock.release()
        raise exceptions.ConfigurationError(err_message)

    lock.release()


def get_log_file_content(log_file=None):
    try:
        if log_file is None:
            log_file = get_log_filename()
        lock = LockFile(log_file)
        lock.acquire()
        with open(log_file, 'r') as f:
            lines = f.read().splitlines()
            f.close()
        lock.release()
        file_content = ""
        for line in lines:
            file_content += "{0}<br/>".format(line)
        return file_content
    except:
        err_message = "Failures while locking or using {0}".format(log_file)
        lock.release()
        raise exceptions.ConfigurationError(err_message)


def get_log_filename():
    if HOST_POOL_LOG_FILE in os.environ:
        return os.environ[HOST_POOL_LOG_FILE]
    return "/tmp/hostpoolservice.log"


def get_arg_value(arg_key, arg_value=''):
    if request:
        if request.args:
            write_to_log('get_arg_value', "request contains args")
            curr_arg_value = request.args.get(arg_key, None)
            if curr_arg_value is not None:
                write_to_log('get_arg_value', "request args '{0}' is {1}".format(arg_key, curr_arg_value))
                return curr_arg_value
    return arg_value