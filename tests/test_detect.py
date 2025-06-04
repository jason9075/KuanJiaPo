import unittest
import sys
import types
import os

# Provide lightweight stubs for external dependencies so that src.detect can be
# imported without installing heavy packages.
dummy_module = types.ModuleType("dummy")
sys.modules.setdefault("cv2", dummy_module)
sys.modules.setdefault("requests", dummy_module)

dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv_stub)

deepface_stub = types.ModuleType("deepface")
deepface_stub.DeepFace = object
sys.modules.setdefault("deepface", deepface_stub)

os.environ.setdefault("INTERVAL_SEC", "1")
os.environ.setdefault("PERSON_INTERVAL_MIN", "1")
os.environ.setdefault("FACE_CONF_THR", "0.5")

class SimpleNP:
    @staticmethod
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    class linalg:
        @staticmethod
        def norm(v):
            return sum(x * x for x in v) ** 0.5

sys.modules.setdefault("numpy", SimpleNP)
import numpy as np  # noqa: E402

from src import detect

is_similar = detect.is_similar
Person = detect.Person

class TestIsSimilar(unittest.TestCase):
    def test_identical_vectors(self):
        v1 = [1.0, 2.0, 3.0]
        v2 = [1.0, 2.0, 3.0]
        self.assertTrue(is_similar(v1, v2))

    def test_different_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, -1.0, 0.0]
        self.assertFalse(is_similar(v1, v2))

class TestPerson(unittest.TestCase):
    def test_person_uuid(self):
        person = Person([0.1, 0.2, 0.3])
        self.assertIsInstance(person.uuid, str)

if __name__ == '__main__':
    unittest.main()
