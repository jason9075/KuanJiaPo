import unittest
from unittest.mock import MagicMock
import sys
import types

# Provide stub for MySQLdb to avoid requiring the real library
mysql_stub = types.ModuleType("MySQLdb")
mysql_stub.connect = MagicMock()
mysql_stub.cursors = types.SimpleNamespace(DictCursor=object)
mysql_stub.OperationalError = Exception
sys.modules.setdefault("MySQLdb", mysql_stub)

pytz_stub = types.ModuleType("pytz")
pytz_stub.timezone = lambda *args, **kwargs: types.SimpleNamespace()
sys.modules.setdefault("pytz", pytz_stub)

import src.web as web

mysql_stub.connect.reset_mock()

class TestEnsureDbConnection(unittest.TestCase):
    def test_reconnect_on_operational_error(self):
        mock_db = MagicMock()
        mock_db.ping.side_effect = mysql_stub.OperationalError
        web.db = mock_db

        web.ensure_db_connection()

        mock_db.close.assert_called_once()
        mysql_stub.connect.assert_called_once()

if __name__ == '__main__':
    unittest.main()
