from app.external.min_wage import load_min_wage


def test_known_years():
    table = load_min_wage()
    assert table[2026] == 10320
    assert table[2025] == 10030


def test_covers_2014_to_2026_with_int_keys():
    assert sorted(load_min_wage()) == list(range(2014, 2027))
