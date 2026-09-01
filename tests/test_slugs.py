from generator.slugs import Slugger

def test_lowercases_and_hyphenates_spaces():
    assert Slugger().slug("Green Party") == "green-party"

def test_underscores_are_preserved_backticks_removed():
    # source: "## Setting `cert_loc`" -> Hugo emits id="setting-cert_loc"
    assert Slugger().slug("Setting `cert_loc`") == "setting-cert_loc"

def test_punctuation_is_deleted_not_replaced():
    # backticks vanish rather than becoming separators
    assert Slugger().slug("Switch the `if` and `else` branches") == \
        "switch-the-if-and-else-branches"

def test_consecutive_spaces_are_not_collapsed():
    # source: "## First a  point of terminology" (two spaces)
    # Hugo emits id="first-a--point-of-terminology"
    assert Slugger().slug("First a  point of terminology") == \
        "first-a--point-of-terminology"

def test_duplicates_get_numeric_suffixes():
    # one post has four "### Detection" headings
    s = Slugger()
    assert [s.slug("Detection") for _ in range(4)] == \
        ["detection", "detection-1", "detection-2", "detection-3"]

def test_dedupe_is_per_document():
    assert Slugger().slug("Detection") == "detection"
    assert Slugger().slug("Detection") == "detection"

def test_strips_inline_html():
    assert Slugger().slug("A <em>word</em> here") == "a-word-here"
