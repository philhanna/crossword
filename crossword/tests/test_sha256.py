from crossword import sha256


class TestSha256:

    def test_same(self):
        cs1 = sha256("Hello")
        cs2 = sha256("Hello")
        assert cs1 == cs2

    def test_different(self):
        cs1 = sha256("Hello1")
        cs2 = sha256("Hello2")
        assert cs1 != cs2

    def test_none(self):
        x = None
        sha = sha256(x)
        assert sha is not None

    def test_int(self):
        x = 17
        sha = sha256(x)
        assert sha is not None

    def test_obj(self):
        x = object()
        sha = sha256(x)
        assert sha is not None
