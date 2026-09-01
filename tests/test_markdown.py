from pathlib import Path
from generator.content import parse_post
from generator.markdown import render, summary

def test_headings_get_ids():
    assert 'id="green-party"' in render("## Green Party")

# Pins the auto-summary truncation boundary (Hugo's default SummaryLength,
# 70 words) against two real posts with different shapes, each verified
# against Hugo's own real output (captured with
# `TZ=America/Los_Angeles direnv exec . hugo --destination ...`, matching
# the site's real deploy environment -- see task-6-report.md's "word-count
# boundary" section for the full investigation, including the one shape
# this rule still gets wrong).
def test_summary_stops_after_a_paragraph_crossing_the_limit():
    # Threshold is crossed inside a blockquote (a paragraph, then more
    # nested content) -- a blockquote is a valid place to stop, just like
    # a paragraph: Hugo's real summary ends exactly at the blockquote,
    # 91 words, nothing further.
    post = parse_post(Path("content/posts/clients-as-a-pitfall.md"))
    text = summary(post.body)
    assert len(text.split()) == 91
    assert text.endswith("you have to assume it will never happen.")

def test_summary_runs_on_past_a_heading_crossing_the_limit():
    # Threshold is crossed inside a heading -- NOT a valid place to stop:
    # Hugo's real summary runs on through the entire next paragraph
    # (97 words) before stopping.
    post = parse_post(Path("content/posts/dynamically-typed-statically-typed-metaprogramming.md"))
    text = summary(post.body)
    assert len(text.split()) == 97
    assert text.endswith("If you’re sure you know, you can skip this.")

def test_strikethrough_uses_del_not_s():
    # Goldmark emits <del>; markdown-it-py's default is <s>
    out = render("~~gone~~")
    assert "<del>gone</del>" in out
    assert "<s>" not in out

def test_bare_domain_is_not_linkified():
    # "coverage.py" must stay text: .py is not a TLD we accept
    assert "<a href" not in render("I used coverage.py for this.")

def test_real_url_is_still_linkified():
    assert '<a href="https://example.com/x">' in render("See https://example.com/x")

def test_definition_lists_render():
    out = render("Term\n:   Definition\n")
    assert "<dl>" in out and "<dt>" in out and "<dd>" in out

def test_images_are_lazy():
    out = render("![alt](/img/x.png)")
    assert 'loading="lazy"' in out
    assert 'src="/img/x.png"' in out
    assert 'alt="alt"' in out

def test_accepted_drift_directional_quotes():
    # we deliberately do NOT match Goldmark here; it makes every ' into a right
    # quote, we produce proper directional quotes
    assert "‘then’" in render("'then'")

def test_code_block_structure_preserved():
    out = render("```elm\nx = 1\n```")
    assert "<pre" in out and "</pre>" in out

def test_highlighted_block_is_not_double_wrapped():
    # the custom fence rule must produce exactly one <pre>, wrapped in
    # exactly one Chroma-style <div class="highlight">.
    out = render("```python\nx = 1\n```")
    assert out.count("<pre") == 1
    assert out.count('<div class="highlight">') == 1

def test_highlighted_block_has_chroma_wrapper_and_attrs():
    # matches Hugo/Chroma exactly: div.highlight is styled in main.css and
    # referenced by chroma-mod.css/scroll-bar.css, so it must sit outside
    # the <pre>; tabindex/color/tab-size on <pre> matter visually even
    # though they're inside the region compare.py's normalise() ignores.
    out = render("```make\nall:\n\techo hi\n```")
    assert out.startswith(
        '<div class="highlight"><pre tabindex="0" '
        'style="color:#f8f8f2;background-color:#272822;'
        '-moz-tab-size:4;-o-tab-size:4;tab-size:4;-webkit-text-size-adjust:none;">'
        '<code class="language-make" data-lang="make">'
    )
    assert out.rstrip().endswith("</code></pre></div>")

def test_highlighted_block_has_differentiated_tokens():
    # a known language must come out with per-token colour spans, not flat
    # escaped text.
    out = render("```python\nx = 1  # comment\n```")
    assert "<span style=" in out

def test_unlabelled_block_has_no_colour_spans():
    out = render("```\nx = 1\n```")
    assert "<span style=" not in out

def test_unknown_language_falls_back_to_plain():
    out = render("```nosuchlang\nx = 1\n```")
    assert "<span style=" not in out
    assert out.count("<pre") == 1

def test_h1_heading_gets_an_id():
    # a body-level `# heading` renders as <h1>, and it must get an id too,
    # same as <h2>..<h6> -- Hugo emits anchor ids for all of them.
    assert 'id="conclusion"' in render("# Conclusion")

def test_image_attribute_order_matches_hugo():
    # Hugo's render-image.html hook merges alt/src/title/loading into one
    # map and ranges over it, which Go sorts alphabetically: alt, loading, src.
    out = render("![alt](/img/x.png)")
    assert '<img alt="alt" loading="lazy" src="/img/x.png">' in out

def test_bare_email_adjacent_to_quote_is_linkified():
    # real text from content/posts/gmail-and-spam.md: a quoted address
    # immediately preceded by an apostrophe must still be autolinked.
    out = render("such as 'lovesakina33@gmail.com'.")
    assert '<a href="mailto:lovesakina33@gmail.com">' in out

def test_raw_html_img_is_not_rewritten():
    # an author-typed <img> tag is raw HTML, not markdown-it's own image
    # node -- our lazy-loading transform must not touch it.
    out = render('<img src="/img/x.png">')
    assert 'loading="lazy"' not in out
    assert '<img src="/img/x.png">' in out

def test_raw_html_s_is_not_rewritten():
    # an author-typed <s> tag is raw HTML, not markdown-it's own
    # strikethrough node -- our <del> transform must not touch it.
    out = render("<s>manual</s>")
    assert "<s>manual</s>" in out
    assert "<del>" not in out
