########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


import errno
import fcntl
import itertools
import os
import random
import select
import socket
import time
import threading
import unittest

import subprocess32
from cloudify_hostpool.hosts import scan


_MAGIC_NUMBER_LISTEN_PORT_RANGE = (10000, 11000, 3)
_MAGIC_NUMBER_CONNECTION_PORT_RANGE = (20000, 21000, 3)

_MAGIC_NUMBER_DEFAULT_JOIN_TIMEOUT = 5
_MAGIC_NUMBER_DEFAULT_BLOCK_TIME = 1
_MAGIC_NUMBER_ENDPOINTS_MULTIPLIER = 5

_SIDE_LISTEN = 0
_SIDE_CONNECT = 1

_SUPERUSER_PRIVILEGES = (os.geteuid() == 0)
_REQUIRES_SUPERUSER_PRIVILEGES_TEXT = 'Superuser privileges required.'


class ScanTests(unittest.TestCase):

    """
    **Real** scan (integration) tests
    """

    def __init__(self, *args, **kwargs):
        super(ScanTests, self).__init__(*args, **kwargs)
        self._set_up_ports()
        self.endpoints = zip(itertools.repeat('127.0.0.1'),
                             itertools.chain(self._free_ports,
                                             self._invalid_ports))
        self.listening_thread = None
        self._blocker_thread = None

    def setUp(self):
        random.shuffle(self.endpoints)
        self.listening_thread = _SocketThread(self._free_ports)

    def tearDown(self):
        if self.listening_thread is not None \
                and self.listening_thread.isAlive():
            self.listening_thread.stop()
            self.listening_thread.join(_MAGIC_NUMBER_DEFAULT_JOIN_TIMEOUT)
            # Just to be safe.
            assert not self.listening_thread.isAlive()
            self.listening_thread = None
        if self._blocker_thread is not None:
            self._blocker_thread.join(_MAGIC_NUMBER_DEFAULT_JOIN_TIMEOUT)
            # Just to be safe.
            assert not self._blocker_thread.isAlive()
            self._blocker_thread = None

    def test_normal_scan(self):

        """
        A normal use case.

        Checks whether the scan mechanism works as expected.
        """

        self.listening_thread.start()
        results = scan.scan(self.endpoints)
        self._check_results(results)

    @unittest.skipUnless(_SUPERUSER_PRIVILEGES,
                         _REQUIRES_SUPERUSER_PRIVILEGES_TEXT)
    def test_blocked_scan(self):

        """
        Checks whether scanner does not hang if packets are dropped.
        """

        self.listening_thread.start()
        self._start_port_blocker()
        results = scan.scan(self.endpoints)
        self._check_results(results)

    @unittest.skipIf('DONT_RUN_REALLY_LONG_TESTS' in os.environ,
                     'Requested to skip this really long test.')
    @unittest.skipUnless(_SUPERUSER_PRIVILEGES,
                         _REQUIRES_SUPERUSER_PRIVILEGES_TEXT)
    def test_fully_dropped_endpoint_scan(self):

        """
        An edge case.

        Checks whether the scan mechanism works correctly
        if packets on the target endpoint are endlessly dropped.
        """

        port = self._invalid_ports[0]
        _iptables_block(port)
        # This may take a while (depends on the operating system)...
        try:
            result = scan.scan([('127.0.0.1', self._invalid_ports[0])])
            self.assertEqual(len(result), 1)
            self._check_results(result)
        finally:
            _iptables_unblock(port)

    def test_no_endpoints_scan(self):

        """
        An edge case.

        Checks whether the scan mechanism works correctly with
        a single endpoint.
        """

        result = scan.scan([])
        self.assertEqual(len(result), 0)

    def test_single_open_endpoint_scan(self):

        """"
        An edge case.

        Checks whether the scan mechanism works correctly with
        a single endpoint that is open.
        """

        self.listening_thread.start()
        result = scan.scan([('127.0.0.1', self._free_ports[0])])
        self.assertEqual(len(result), 1)
        self._check_results(result)

    def test_single_closed_endpoint_scan(self):

        """
        An edge case.

        Checks whether the scan mechanism works correctly with
        a single endpoint that is closed.
        """

        result = scan.scan([('127.0.0.1', self._invalid_ports[0])])
        self.assertEqual(len(result), 1)
        self._check_results(result)

    @unittest.skipUnless(_SUPERUSER_PRIVILEGES,
                         _REQUIRES_SUPERUSER_PRIVILEGES_TEXT)
    def test_single_blocked_endpoint_scan(self):

        """
        An edge case.

        Checks whether the scan mechanism works correctly with
        a single endpoint that is initially blocked.
        """

        self._start_port_blocker([self._invalid_ports[0]])
        result = scan.scan([('127.0.0.1', self._invalid_ports[0])])
        self.assertEqual(len(result), 1)
        self._check_results(result)

    @unittest.skipUnless(_SUPERUSER_PRIVILEGES,
                         _REQUIRES_SUPERUSER_PRIVILEGES_TEXT)
    def test_all_closed_blocked_scan(self):

        """
        An edge case.

        Checks whether the scan mechanism works correctly with
        only blocked endpoints.
        """

        self.listening_thread.start()
        self._start_port_blocker()
        results = scan.scan(self.endpoints)
        self._check_results(results)

    def test_normal_scan_with_multiple_endpoints(self):

        """
        A normal use case.

        Checks whether the scan mechanism works as expected.
        """

        endpoints = self.endpoints * _MAGIC_NUMBER_ENDPOINTS_MULTIPLIER
        random.shuffle(endpoints)
        self.listening_thread.start()
        results = scan.scan(endpoints)
        self._check_results(results)

    def _start_port_blocker(self, ports=None):
        # Just to be safe.
        assert self._blocker_thread is None
        if ports is None:
            ports = self._invalid_ports
        self._blocker_thread = _BlockerThread(ports)
        self._blocker_thread.start()

    def _set_up_ports(self):
        begin, end, count = _MAGIC_NUMBER_LISTEN_PORT_RANGE
        self._free_ports = _find_ports(begin, end, count, _SIDE_LISTEN)
        begin, end, count = _MAGIC_NUMBER_CONNECTION_PORT_RANGE
        self._invalid_ports = _find_ports(begin, end, count, _SIDE_CONNECT)

    def _check_results(self, results):
        # all open ports are reported as open
        self.assertTrue(
            all(results[hp]
                for hp in itertools.izip(itertools.repeat('127.0.0.1'),
                                         self._free_ports)
                if hp in results)
        )
        # all invalid ports are reported as closed
        self.assertFalse(
            any(results[hp]
                for hp in itertools.izip(itertools.repeat('127.0.0.1'),
                                         self._invalid_ports)
                if hp in results)
        )


class _SynchronisedStartThread(threading.Thread):
    #   Synchronises thread **and** its main function to start
    #   using a condition variable.

    def __init__(self):
        super(_SynchronisedStartThread, self).__init__()
        self.cv = threading.Condition()
        self._cv_notify = True

    def start(self):
        self.cv.acquire()
        super(_SynchronisedStartThread, self).start()
        self.cv.wait()
        self.cv.release()

    def release_and_notify_if_needed(self):
        if self._cv_notify:
            self.cv.notifyAll()
            self.cv.release()
            self._cv_notify = False


class _SocketThread(_SynchronisedStartThread):
    #   Listens on the given ports.

    def __init__(self, ports):
        super(_SocketThread, self).__init__()
        self._ports = ports
        self._running = False

    def stop(self):
        self._running = False
        try:
            #   See below.
            os.close(self._pipe_fd_w)
        except OSError:
            pass

    def run(self):
        self.cv.acquire()
        self._running = True
        #   Read end will be used in blocking `pselect` calls.
        #   Write end will be used in `stop` to break
        #   the aforementioned `pselect` call.
        pipe_fd_r, self._pipe_fd_w = os.pipe()
        sockets = []
        try:
            for port in self._ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                flags = fcntl.fcntl(sock.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(sock.fileno(),
                            fcntl.F_SETFL, flags | os.O_NONBLOCK)
                sock.bind(('127.0.0.1', port))
                sock.listen(1)
                sockets.append(sock)
            self.release_and_notify_if_needed()
            while self._running:
                fds = [s.fileno() for s in sockets]
                #   See above.
                fds.append(pipe_fd_r)
                _ = select.select(fds, [], [], None)
                #   The thread could have been interrupted with `stop`.
                if not self._running:
                    break
                for sock in sockets:
                    try:
                        conn, _ = sock.accept()
                    except socket.error as e:
                        if e.errno != errno.EAGAIN:
                            raise
                    else:
                        conn.close()
        finally:
            #   Both pipe ends are closed just to be elegant.
            for fd in pipe_fd_r, self._pipe_fd_w:
                try:
                    os.close(fd)
                except OSError:
                    pass
            self._pipe_fd_w = None
            for sock in sockets:
                sock.close()
            self.release_and_notify_if_needed()


class _BlockerThread(_SynchronisedStartThread):
    #   Sets up `iptables` (**both** ways).

    def __init__(self, ports, sleep_time=_MAGIC_NUMBER_DEFAULT_BLOCK_TIME):
        super(_BlockerThread, self).__init__()
        self._ports = ports
        self._sleep_time = sleep_time

    def run(self):
        self.cv.acquire()
        try:
            for port in self._ports:
                _iptables_block(port)
            self.release_and_notify_if_needed()
            time.sleep(self._sleep_time)
        finally:
            for port in self._ports:
                _iptables_unblock(port)
            self.release_and_notify_if_needed()


def _check_port_listen(port_number):
    #   Finds ports which current process will be able
    #   to **listen** on.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('127.0.0.1', port_number))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            return False
        raise
    else:
        sock.close()
        return True


def _check_port_connect(port_number):
    #   Finds ports which are **not** open.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', port_number))
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED:
            return True
        raise
    else:
        sock.close()
        return False


_CHECK_PORT_FUN = {_SIDE_LISTEN: _check_port_listen,
                   _SIDE_CONNECT: _check_port_connect}


def _find_ports(range_begin, range_end, count, side):
    result = []
    for p in xrange(range_begin, range_end):
        if _CHECK_PORT_FUN[side](p):
            result.append(p)
            if len(result) >= count:
                return result
    raise RuntimeError('Could not find required ports')


def _call(arguments):
    process = subprocess32.Popen(arguments,
                                 stdin=open(os.devnull),
                                 stdout=open(os.devnull))
    process.wait()
    # Just to be safe.
    assert process.returncode == 0


def _iptables_block(port_number, position=1):
    _call(['iptables',
           '-I', 'INPUT', str(position),
           '-i', 'lo',
           '-p', 'tcp',
           '-s', '127.0.0.1',
           '-d', '127.0.0.1',
           '--dport', str(port_number),
           '-j', 'DROP'])


def _iptables_unblock(port_number):
    _call(['iptables',
           '-D', 'INPUT',
           '-i', 'lo',
           '-p', 'tcp',
           '-s', '127.0.0.1',
           '-d', '127.0.0.1',
           '--dport', str(port_number),
           '-j', 'DROP'])
