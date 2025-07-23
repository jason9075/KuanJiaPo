import unittest
from unittest.mock import MagicMock
import sys
import types
import asyncio
import json

# Provide stub for MySQLdb to avoid requiring the real library
mysql_stub = types.ModuleType("MySQLdb")
mysql_stub.connect = MagicMock()
mysql_stub.cursors = types.SimpleNamespace(DictCursor=object)
mysql_stub.OperationalError = Exception
sys.modules.setdefault("MySQLdb", mysql_stub)

pytz_stub = types.ModuleType("pytz")
pytz_stub.timezone = lambda *args, **kwargs: types.SimpleNamespace()
sys.modules.setdefault("pytz", pytz_stub)

# Stub FastAPI and related modules to avoid installing the real package
fastapi_stub = types.ModuleType("fastapi")
fastapi_stub.FastAPI = MagicMock()
fastapi_stub.Request = object
fastapi_stub.Query = lambda *args, **kwargs: None
fastapi_stub.WebSocket = object
fastapi_stub.WebSocketDisconnect = Exception
fastapi_stub.UploadFile = object
fastapi_stub.File = lambda *args, **kwargs: None
fastapi_stub.Form = lambda *args, **kwargs: None

fastapi_staticfiles = types.ModuleType("fastapi.staticfiles")
fastapi_staticfiles.StaticFiles = MagicMock()

fastapi_responses = types.ModuleType("fastapi.responses")
fastapi_responses.HTMLResponse = MagicMock()
fastapi_responses.JSONResponse = MagicMock()
fastapi_responses.Response = MagicMock()
fastapi_responses.StreamingResponse = MagicMock()
fastapi_responses.FileResponse = MagicMock()

sys.modules.setdefault("fastapi", fastapi_stub)
sys.modules.setdefault("fastapi.staticfiles", fastapi_staticfiles)
sys.modules.setdefault("fastapi.responses", fastapi_responses)

starlette_background = types.ModuleType("starlette.background")
starlette_background.BackgroundTask = MagicMock()
sys.modules.setdefault("starlette.background", starlette_background)

uvicorn_stub = types.ModuleType("uvicorn")
uvicorn_stub.run = MagicMock()
sys.modules.setdefault("uvicorn", uvicorn_stub)

dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv_stub)

prometheus_stub = types.ModuleType("prometheus_client")
prometheus_stub.Counter = MagicMock(return_value=MagicMock())
prometheus_stub.generate_latest = MagicMock(return_value=b"")
prometheus_stub.CONTENT_TYPE_LATEST = "text/plain"
sys.modules["prometheus_client"] = prometheus_stub

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


class TestConnectionManager(unittest.TestCase):
    def test_broadcast_excludes_sender(self):
        cm = web.ConnectionManager()

        class DummyWS:
            def __init__(self):
                self.sent = []

            async def accept(self):
                pass

            async def send_text(self, msg):
                self.sent.append(msg)

        ws1 = DummyWS()
        ws2 = DummyWS()

        loop = asyncio.new_event_loop()
        loop.run_until_complete(cm.connect(ws1))
        loop.run_until_complete(cm.connect(ws2))
        loop.run_until_complete(cm.broadcast("hello", ws1))

        count1 = json.dumps({"type": "count", "count": 1})
        count2 = json.dumps({"type": "count", "count": 2})
        self.assertEqual(ws1.sent, [count1, count2])
        self.assertEqual(ws2.sent, [count2, "hello"])


if __name__ == "__main__":
    unittest.main()
