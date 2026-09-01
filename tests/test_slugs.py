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

def test_literal_numbered_heading_does_not_collide():
    s = Slugger()
    assert [s.slug(t) for t in ["Detection", "Detection", "Detection 1", "Detection"]] == \
        ["detection", "detection-1", "detection-1-1", "detection-2"]

def test_empty_slug_falls_back_to_heading():
    s = Slugger()
    assert s.slug("???") == "heading"
    assert s.slug("!!!") == "heading-1"

def test_no_duplicate_ids_ever():
    s = Slugger()
    ids = [s.slug(t) for t in ["A", "A", "A 1", "A", "A 1", "A-1"]]
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"
