import unittest

from crossword import sha256


class TestSha256(unittest.TestCase):

    def test_same(self):
        cs1 = sha256("Hello")
        cs2 = sha256("Hello")
        self.assertEqual(cs1, cs2)

    def test_different(self):
        cs1 = sha256("Hello1")
        cs2 = sha256("Hello2")
        self.assertNotEqual(cs1, cs2)

    def test_none(self):
        x = None
        sha = sha256(x)
        self.assertIsNotNone(sha)

    def test_int(self):
        x = 17
        sha = sha256(x)
        self.assertIsNotNone(sha)

    def test_obj(self):
        x = object()
        sha = sha256(x)
        self.assertIsNotNone(sha)
