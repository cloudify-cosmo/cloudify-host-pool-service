# #######
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.

import tempfile
import testtools
import sqlite3

from cloudify_hostpool.storage import sqlite


class SQLiteTest(testtools.TestCase):

    @classmethod
    def setUpClass(cls):
        super(SQLiteTest, cls).setUpClass()
        _, cls.tempfile = tempfile.mkstemp()

    def setUp(self):
        super(SQLiteTest, self).setUp()
        self.db = sqlite.SQLiteStorage(self.tempfile)

    def tearDown(self):
        super(SQLiteTest, self).tearDown()
        with self.db.connect() as cursor:
            cursor.execute('DROP TABLE {0}'
                           .format(sqlite.SQLiteStorage.TABLE_NAME))

    def test_get_all_empty(self):
        result = self.db.get_hosts()
        self.assertEqual(result, [])

    def test_add_host(self):
        host = {
            'host': '127.0.0.1',
            'public_address': '127.0.0.1',
            'port': 22,
            'auth': {},
            'host_id': None,
            'alive': False,
            'reserved': False
        }
        self.db.add_host(host)
        result = self.db.get_hosts()
        self.assertEqual(len(result), 1)
        db_host = result[0]
        self.assertEqual(db_host, host)

    def test_add_bad_host(self):
        host = {
            'port': 22,
            'auth': None,
            'host_id': None,
            'alive': False,
            'reserved': False
        }
        self.assertRaises(sqlite3.OperationalError,
                          self.db.add_host, host)

    def test_get_filtered_hosts(self):
        self._add_hosts()

        result = self.db.get_hosts()
        self.assertEqual(len(result), len(self.host_list))

        result = self.db.get_hosts(port=1000)
        self.assertEqual(len(result), 3)

        result = self.db.get_hosts(alive=True)
        self.assertEqual(len(result), 3)

        result = self.db.get_hosts(alive=True, port=1000)
        self.assertEqual(len(result), 2)

        result = self.db.get_hosts(host_id='test')
        self.assertEqual(len(result), 1)

    def test_update_compare(self):
        self.db.add_host({
            'host': '127.0.0.1',
            'public_address': '127.0.0.1',
            'port': 22,
            'auth': {},
            'host_id': None,
            'alive': True,
            'reserved': False
        })
        _, changed = self.db.update_host(
            global_id=1,
            new_values={'reserved': True},
            old_values={'reserved': True})
        self.assertFalse(changed)

    def test_update_host(self):
        self._add_hosts()
        result = self.db.get_hosts()
        host = result[0]
        host_update = {
            'reserved': True
        }
        updated_host, _ = self.db.update_host(host['global_id'], host_update)
        self.assertEqual(updated_host['global_id'], host['global_id'])
        self.assertNotEqual(updated_host['reserved'], host['reserved'])
        self.assertEqual(updated_host['reserved'], host_update['reserved'])
        updated_host2, _ = self.db.update_host(host['global_id'], host_update)
        self.assertEqual(updated_host, updated_host2)

    def test_get_host_filter(self):
        self._add_hosts()
        hosts = self.db.get_hosts()
        db_host = hosts[0]
        host = self.db.get_hosts(alive=True)[0]
        self.assertEqual(db_host, host)

    def _add_hosts(self):
        self.host_list = [
            {
                'host': '127.0.0.1',
                'public_address': '127.0.0.1',
                'port': '22',
                'auth': {},
                'host_id': None,
                'alive': True,
                'reserved': False
            },
            {
                'host': '127.0.0.1',
                'public_address': '127.0.0.1',
                'port': 1000,
                'auth': {},
                'host_id': None,
                'alive': False,
                'reserved': False
            },
            {
                'host': '10.0.0.1',
                'public_address': '10.0.0.1',
                'port': 1000,
                'auth': {},
                'host_id': None,
                'alive': True,
                'reserved': False
            },
            {
                'host': '10.0.0.1',
                'public_address': '10.0.0.1',
                'port': 1000,
                'auth': {},
                'host_id': 'test',
                'alive': True,
                'reserved': False
            }
        ]
        for host in self.host_list:
            self.db.add_host(host)
