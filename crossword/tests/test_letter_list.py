from crossword.domain.letter_list import regexp


class TestLetterList:

    def test_with_all(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        assert "." == regexp(letters)

    def test_with_small_straight(self):
        letters = "ABCD"
        assert "[A-D]" == regexp(letters)

    def test_with_gaps(self):
        letters = "BCDKLMWXZ"
        assert "[^AE-JN-VY]" == regexp(letters)

    def test_with_all_but_j_and_q(self):
        letters = "ABCDEFGHIKLMNOPRSTUVWXYZ"
        assert "[^JQ]" == regexp(letters)

    def test_with_all_but_z(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXY"
        assert "[^Z]" == regexp(letters)

    def test_with_single_letter(self):
        letters = "S"
        assert "S" == regexp(letters)

    def test_with_empty_pattern(self):
        letters = ""
        assert "" == regexp(letters)
