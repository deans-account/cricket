from database.database import Database


def test_initialise(tmp_path):
    path = tmp_path / "test.sqlite"
    Database(path).initialise()
    assert path.exists()
