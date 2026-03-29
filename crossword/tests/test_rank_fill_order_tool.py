import importlib.util
from pathlib import Path

from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
from crossword.tests import TestPuzzle


TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "user" / "rank_fill_order.py"


def load_main():
    spec = importlib.util.spec_from_file_location("rank_fill_order_tool", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


class TestRankFillOrderTool:

    def test_main_prints_ranked_slots(self, tmp_path, capsys):
        main = load_main()
        db_path = tmp_path / "rank-fill.db"
        adapter = SQLitePersistenceAdapter(str(db_path))
        adapter.init_schema()
        adapter.save_puzzle(1, "atlantic", TestPuzzle.create_atlantic_puzzle())

        exit_code = main(["atlantic", "--dbfile", str(db_path), "--top", "3"])

        captured = capsys.readouterr()
        lines = captured.out.strip().splitlines()

        assert exit_code == 0
        assert lines[0] == "Fill priority for puzzle 'atlantic':"
        assert lines[1].startswith("12D ")
        assert "critical=yes" in lines[1]
        assert lines[2].startswith("14A ")
        assert lines[3].startswith(("3D ", "5D ", "11A ", "18A "))

    def test_main_returns_error_for_missing_puzzle(self, tmp_path, capsys):
        main = load_main()
        db_path = tmp_path / "rank-fill.db"
        adapter = SQLitePersistenceAdapter(str(db_path))
        adapter.init_schema()

        exit_code = main(["missing", "--dbfile", str(db_path)])

        captured = capsys.readouterr()

        assert exit_code == 1
        assert "Error:" in captured.out
