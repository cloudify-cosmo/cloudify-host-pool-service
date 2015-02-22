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


import itertools
import random
import testtools

import mock

from cloudify_hostpool.hosts import scan


class SplitTests(testtools.TestCase):

    @classmethod
    def setUpClass(cls):
        super(SplitTests, cls).setUpClass()
        cls._patches = {
            'fd_res_lim': mock.patch('resource.getrlimit',
                                     mock.MagicMock(return_value=(20, None))),
            'o_fds': mock.patch(
                'cloudify_hostpool.hosts.scan._open_file_descriptors',
                mock.MagicMock(return_value=2))
        }

    def setUp(self):
        super(SplitTests, self).setUp()
        for patch in self._patches.itervalues():
            patch.start()

    def tearDown(self):
        super(SplitTests, self).tearDown()
        for patch in self._patches.itervalues():
            patch.stop()

    def test_split_lengths(self):

        """
        A normal use case.

        Checks whether length of individual chunks does not exceed
        resource limits.
        """

        rng = int(self._patches['fd_res_lim'].new.return_value[0] * 5)
        lim = int(scan._file_descriptor_resource_limit() *
                  scan._MAGIC_NUMBER_SPLIT_UPPER_THRESHOLD)
        for l in scan._split(range(rng)):
            self.assertLessEqual(len(l), lim)

    def test_empty_list(self):

        """
        An edge case.

        Checks whether an empty list is correctly processed.
        """

        l = list(scan._split([]))
        self.assertEqual(l, [])

    def test_single_element(self):

        """
        An edge case.

        Checks whether a single element is correctly processed.
        """

        l = list(scan._split(['value']))
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0], ['value'])

    def test_limit_exceeded(self):

        """
        A rare case

        Checks whether length of individual chunks is always 1
        after FD limit is exceeded.
        """

        lim_u = int(scan._file_descriptor_resource_limit() *
                    scan._MAGIC_NUMBER_SPLIT_UPPER_THRESHOLD)
        lim_l = int(scan._file_descriptor_resource_limit() *
                    scan._MAGIC_NUMBER_SPLIT_LOWER_THRESHOLD)
        rng = int(self._patches['fd_res_lim'].new.return_value[0] * lim_l)
        o_fd_mock = self._patches['o_fds'].new
        self.assertLess(o_fd_mock.return_value, lim_l)
        for l in scan._split(range(rng)):
            if o_fd_mock.return_value < lim_l:
                self.assertTrue(1 < len(l) <= lim_u)
                o_fd_mock.return_value += 1
            else:
                self.assertEqual(len(l), 1)
        self.assertGreaterEqual(o_fd_mock.return_value, lim_l)


class FillEndpointsTests(testtools.TestCase):

    def test_no_fill(self):

        """
        A normal use case.

        Check whether a fully filled list does not get overwritten.
        """

        l1 = zip(xrange(10), itertools.repeat('a'))
        l2 = scan._fill_endpoints(l1, 'a')
        self.assertEqual(l1, l2)

    def test_all_fill(self):

        """
        A normal use case

        Checks if a list without ports is properly filled.
        """

        l1 = range(10)
        l2 = scan._fill_endpoints(l1, 'a')
        for e1, e2 in itertools.izip(l1, l2):
            self.assertEqual(e2, (e1, 'a'))

    def test_mixed(self):

        """
        A normal use case

        Checks if only the desired parts of a list are filled.
        """

        l1 = ['a', ('b1', 'b2')]
        for i in xrange(10):
            l1.append(random.choice([i, (i, i)]))
        l2 = scan._fill_endpoints(l1, 'c')
        for e1, e2 in itertools.izip(l1, l2):
            if isinstance(e1, tuple):
                self.assertEqual(e1, e2)
            else:
                self.assertEqual(e2, (e1, 'c'))

    def test_empty(self):

        """
        An edge case

        Checks if an empty list stays empty.
        """

        l = scan._fill_endpoints([], 'a')
        self.assertEqual(l, [])

    def test_single_element(self):

        """
        An edge case

        Checks whether a list with a single element does not break
        the function.
        """

        l = scan._fill_endpoints([1], 'a')
        self.assertEqual(l, [(1, 'a')])

    def test_single_tuple(self):

        """
        An edge case

        Checks whether a single tuple does not change.
        """

        l1 = [(1, 'a')]
        l2 = scan._fill_endpoints(l1, 'b')
        self.assertEqual(l1, l2)
