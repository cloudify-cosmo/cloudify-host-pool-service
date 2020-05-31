# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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
'''
    tests.logger
    ~~~~~~~~~~~~
    Tests the debug logger
'''

# pylint: disable=R0201

import os
import json
import logging
import tempfile
import testtools
from testtools import ExpectedException
from testtools.matchers import Equals

from cloudify.mocks import MockCloudifyContext
from cloudify.exceptions import NonRecoverableError

from ..logger import get_hostpool_logger


class LoggerTestCase(testtools.TestCase):
    '''Tests the debug log creator'''
    def setUp(self):
        testtools.TestCase.setUp(self)
        rp = json.loads(json.dumps({'working_directory': '/tmp'}))
        self.ctx = MockCloudifyContext(
            node_id='test_logger',
            node_name='LoggerTestCase',
            runtime_properties=rp)
        self.debug_logfile = os.path.join(
            tempfile.gettempdir(), 'cfy-mock-debug.log')

    def tearDown(self):
        testtools.TestCase.tearDown(self)
        if self.debug_logfile and os.path.exists(self.debug_logfile):
            os.remove(self.debug_logfile)

    def test_logger_non_debug(self):
        '''Tests non-debug logger'''
        mock_logger = get_hostpool_logger('mock',
                                          parent_logger=self.ctx.logger)
        self.assertThat(mock_logger.parent, Equals(self.ctx.logger))

    def test_logger_debug_without_file(self):
        '''Tests debug logger w/o debug log file'''
        mock_logger = get_hostpool_logger('mock',
                                          parent_logger=self.ctx.logger,
                                          debug=True)
        self.assertThat(mock_logger.parent, Equals(self.ctx.logger))
        self.assertThat(mock_logger.level, Equals(logging.DEBUG))

    def test_logger_debug_with_file(self):
        '''Tests debug logger w/ debug log file'''
        mock_logger = get_hostpool_logger('mock',
                                          parent_logger=self.ctx.logger,
                                          debug=True,
                                          log_file=self.debug_logfile)
        self.assertThat(mock_logger.parent, Equals(self.ctx.logger))
        self.assertThat(mock_logger.level, Equals(logging.DEBUG))
        self.assertThat(os.path.exists(self.debug_logfile), Equals(True))

    def test_logger_no_parent_logger(self):
        '''Tests debug logger w/o parent logger'''
        with ExpectedException(NonRecoverableError):
            get_hostpool_logger('mock')
