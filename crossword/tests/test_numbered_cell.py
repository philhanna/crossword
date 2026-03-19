from crossword import NumberedCell


class TestNumberedCell:

    def test_just_r_and_c(self):
        numbered_cell = NumberedCell(1, 3, 2)
        expected = "NumberedCell(seq=1,r=3,c=2)"
        actual = str(numbered_cell)
        assert expected == actual
        assert 0 == numbered_cell.a
        assert 0 == numbered_cell.d

    def test_with_a(self):
        numbered_cell = NumberedCell(1, 3, 2, a=4)
        expected = "NumberedCell(seq=1,r=3,c=2,a=4)"
        actual = str(numbered_cell)
        assert expected == actual
        assert 4 == numbered_cell.a
        assert 0 == numbered_cell.d

    def test_with_d(self):
        numbered_cell = NumberedCell(45, 3, 2, d=46)
        expected = "NumberedCell(seq=45,r=3,c=2,d=46)"
        actual = str(numbered_cell)
        assert expected == actual
        assert 0 == numbered_cell.a
        assert 46 == numbered_cell.d

    def test_with_both(self):
        numbered_cell = NumberedCell(22, 3, 2, d=46, a=12)
        expected = "NumberedCell(seq=22,r=3,c=2,a=12,d=46)"
        actual = str(numbered_cell)
        assert expected == actual
        assert 12 == numbered_cell.a
        assert 46 == numbered_cell.d

    def test_with_both_as_positional(self):
        numbered_cell = NumberedCell(4, 3, 2, 12, 46)
        expected = "NumberedCell(seq=4,r=3,c=2,a=12,d=46)"
        actual = str(numbered_cell)
        assert expected == actual
        assert 12 == numbered_cell.a
        assert 46 == numbered_cell.d

    def test_equals_when_equal(self):
        nca = NumberedCell(17, 3, 2, 4, 5)
        ncb = NumberedCell(17, 3, 2, 3 + 1, 4 + 1)
        assert nca == ncb

    def test_hash(self):
        nc1 = NumberedCell(4, 3, 2, 12, 46)
        assert hash(nc1) is not None

    def test_to_json(self):
        nc = NumberedCell(17, 3, 2, 4, 5)
        expected = '{"seq": 17, "r": 3, "c": 2, "a": 4, "d": 5}'
        actual = nc.to_json()
        assert expected == actual

    def test_from_json(self):
        jsonstr = '{"seq": 17, "r": 3, "c": 2, "a": 4}'
        nc = NumberedCell.from_json(jsonstr)
        assert 17 == nc.seq
        assert 3 == nc.r
        assert 2 == nc.c
        assert 4 == nc.a
        assert 0 == nc.d

    def test_json_round_trip(self):
        nc1 = NumberedCell(17, 3, 2, 4, 5)
        jsonstr = nc1.to_json()
        nc2 = NumberedCell.from_json(jsonstr)
        assert nc1 == nc2

    def notest_print_json(self):
        nc = NumberedCell(17, 3, 2, 4, 5)
        print(f"DEBUG: json={nc.to_json()}")
