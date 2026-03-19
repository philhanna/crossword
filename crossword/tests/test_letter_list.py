from crossword import LetterList


class TestLetterList:

    def test_with_all(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        assert "." == LetterList.regexp(letters)

    def test_with_small_straight(self):
        letters = "ABCD"
        assert "[A-D]" == LetterList.regexp(letters)

    def test_with_gaps(self):
        letters = "BCDKLMWXZ"
        assert "[^AE-JN-VY]" == LetterList.regexp(letters)

    def test_with_all_but_j_and_q(self):
        letters = "ABCDEFGHIKLMNOPRSTUVWXYZ"
        assert "[^JQ]" == LetterList.regexp(letters)

    def test_with_all_but_z(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXY"
        assert "[^Z]" == LetterList.regexp(letters)

    def test_with_single_letter(self):
        letters = "S"
        assert "S" == LetterList.regexp(letters)

    def test_with_empty_pattern(self):
        letters = ""
        assert "" == LetterList.regexp(letters)
