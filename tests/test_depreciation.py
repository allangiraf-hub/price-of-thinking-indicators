from potindicators.depreciation import extract_useful_life_sentences, parse_equipment_life

MSFT = ("The estimated useful lives of our property and equipment are generally "
        "as follows: software developed or acquired for internal use, three years ; "
        "computer equipment, two to six years ; buildings and improvements, "
        "five to 15 years .")


def test_extracts_sentence():
    found = extract_useful_life_sentences(MSFT + " Unrelated sentence.")
    assert len(found) == 1
    assert "computer equipment" in found[0]


def test_parses_word_numbers():
    assert parse_equipment_life(MSFT) == (2, 6)


def test_parses_digit_ranges():
    s = "useful lives: servers and network equipment, 5 to 6 years."
    assert parse_equipment_life(s) == (5, 6)


def test_rejects_nonsense():
    assert parse_equipment_life("useful lives of buildings, 30 years") is None


def test_parses_change_event_shortening():
    from potindicators.depreciation import parse_life_change
    s = ("Effective January 1, 2025 we changed our estimate of the useful lives "
         "of a subset of our servers and networking equipment from six years to five years .")
    assert parse_life_change(s) == (6.0, 5.0)


def test_parses_change_event_decimal():
    from potindicators.depreciation import parse_life_change
    s = "We extended the estimated useful lives of most servers and network assets to 5.5 years."
    assert parse_life_change(s) == (None, 5.5)


def test_change_requires_server_context():
    from potindicators.depreciation import parse_life_change
    assert parse_life_change("we extended the useful lives of buildings to 40 years") is None
