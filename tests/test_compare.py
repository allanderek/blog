"""Regression tests for compare.py's own comparison rules -- in particular
the accepted-drift allow-list (Task 5's Critical review) and the Task 10
feed-content decoding extension (round 2's Critical review, on the same
allow-list boundary but reachable only through a feed's <description>/
<content type="html">). Each test below is one of the six acceptance
criteria from that second review; see the task-10 report's "Round 3
fixes" section for the full diagnosis each corresponds to.

Written against `compare.main()` directly, not the CLI, so a failure here
points straight at the Python traceback/return value rather than parsed
subprocess output.
"""
from pathlib import Path
import compare


def _write(dir_: Path, name: str, content: str) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / name).write_text(content)


# --- 1: a live <script> inside a feed's code-block content ----------------

def test_live_script_inside_feed_code_block_is_detected(tmp_path):
    # The round-2 Critical: Hugo's <description> properly escapes a
    # <script> appearing inside a code sample (twice -- once as normal
    # HTML rendering, once more for XML embedding); the generator's
    # instead has a genuinely live, unescaped <script> tag at the same
    # position, inside what still looks (once decoded) like the same
    # <pre>...</pre> span. Before the round-3 guard, both decoded into a
    # real "<pre"..."</pre>" span and were masked to the same "@@CODE@@"
    # placeholder -- CLEAN. Must be DETECTED now.
    hugo, gen = tmp_path / "hugo", tmp_path / "gen"
    _write(hugo, "index.xml",
           '<rss><channel><item>\n'
           '<description>&lt;pre&gt;&lt;code&gt;&amp;lt;script&amp;gt;'
           'alert(1)&amp;lt;/script&amp;gt;&lt;/code&gt;&lt;/pre&gt;'
           '</description>\n</item></channel></rss>\n')
    _write(gen, "index.xml",
           '<rss><channel><item>\n'
           '<description>&lt;pre&gt;&lt;code&gt;<script>alert(1)</script>'
           '&lt;/code&gt;&lt;/pre&gt;</description>\n</item></channel></rss>\n')
    assert compare.main(str(hugo), str(gen)) == 1


# --- 2: escaped vs. live <script> in page HTML (Task 5's original case) --

def test_escaped_vs_live_script_in_page_html_is_detected(tmp_path):
    hugo, gen = tmp_path / "hugo", tmp_path / "gen"
    _write(hugo, "index.html",
           "<html><body><p>Sample: &lt;script&gt;alert(1)&lt;/script&gt;</p></body></html>\n")
    _write(gen, "index.html",
           "<html><body><p>Sample: <script>alert(1)</script></p></body></html>\n")
    assert compare.main(str(hugo), str(gen)) == 1


# --- 3: a malformed URL query string in page HTML --------------------------

def test_malformed_url_query_string_in_page_html_is_detected(tmp_path):
    hugo, gen = tmp_path / "hugo", tmp_path / "gen"
    _write(hugo, "index.html",
           '<html><body><a href="/x?a=1&amp;b=2">link</a></body></html>\n')
    _write(gen, "index.html",
           '<html><body><a href="/x?a=1&b=2">link</a></body></html>\n')
    assert compare.main(str(hugo), str(gen)) == 1


# --- 4: a corrupted byte inside a binary asset -----------------------------

def test_corrupted_binary_asset_is_detected(tmp_path):
    hugo, gen = tmp_path / "hugo", tmp_path / "gen"
    hugo.mkdir(parents=True)
    gen.mkdir(parents=True)
    data = bytes(range(256)) * 4
    (hugo / "portrait.png").write_bytes(data)
    corrupted = bytearray(data)
    corrupted[len(corrupted) // 2] ^= 0xFF
    (gen / "portrait.png").write_bytes(bytes(corrupted))
    assert compare.main(str(hugo), str(gen)) == 1


# --- 5: two identical trees are CLEAN --------------------------------------

def test_identical_trees_are_clean(tmp_path):
    hugo, gen = tmp_path / "hugo", tmp_path / "gen"
    for d in (hugo, gen):
        _write(d, "index.html", "<html><body><p>Hello, world.</p></body></html>\n")
        _write(d, "index.xml",
               '<rss><channel><item>\n'
               '<description>&lt;p&gt;Hello&amp;rsquo;s world.&lt;/p&gt;</description>\n'
               '</item></channel></rss>\n')
    assert compare.main(str(hugo), str(gen)) == 0


# --- 6: accepted drift inside a feed is still normalised away --------------

def test_accepted_drift_inside_feed_content_is_still_normalised(tmp_path):
    # Two DIFFERENT kinds of already-accepted drift, both inside the same
    # <description> -- an en-dash (goldmark's "&ndash;" reads
    # "&amp;ndash;" once re-escaped for the feed; markdown-it-py's own
    # literal "--" needs no decoding at all) and a code-block colouring
    # difference (Pygments vs. Chroma, "&lt;pre&gt;...&lt;/pre&gt;" in the
    # raw feed text, masked by the same rule a live page's own <pre> gets
    # once decoded). If this stops comparing CLEAN, the round-2 extension
    # has been effectively reverted, not fixed -- see criterion 6.
    hugo, gen = tmp_path / "hugo", tmp_path / "gen"
    _write(hugo, "index.xml",
           '<rss><channel><item>\n'
           '<description>&lt;p&gt;one&amp;ndash;or two&lt;/p&gt; '
           '&lt;pre&gt;&lt;code&gt;&lt;span style=&#34;color:#ff0000&#34;&gt;'
           'foo&lt;/span&gt;&lt;/code&gt;&lt;/pre&gt;</description>\n'
           '</item></channel></rss>\n')
    _write(gen, "index.xml",
           '<rss><channel><item>\n'
           '<description>&lt;p&gt;one--or two&lt;/p&gt; '
           '&lt;pre&gt;&lt;code&gt;&lt;span style=&#34;color:#00ff00&#34;&gt;'
           'foo&lt;/span&gt;&lt;/code&gt;&lt;/pre&gt;</description>\n'
           '</item></channel></rss>\n')
    assert compare.main(str(hugo), str(gen)) == 0
