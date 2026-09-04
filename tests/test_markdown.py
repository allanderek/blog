from pathlib import Path
from generator.content import parse_post
from generator.markdown import (extract_summary, plain, plainify, render,
                                render_entities, summary, word_count)

def test_headings_get_ids():
    assert 'id="green-party"' in render("## Green Party")

# Pins Hugo's auto-summary rule (resources/page/page_markup.go's
# ExtractSummaryFromHTML, at the default SummaryLength of 70) against four
# real posts of deliberately different shapes. Every expectation below was
# read off Hugo's own `.Summary` for that post, captured with
# `TZ=America/Los_Angeles direnv exec . hugo ...` -- the site's real deploy
# environment. The rule is NOT "70 words of prose": it walks the rendered
# HTML paragraph by paragraph, counting whitespace-separated tokens of the
# MARKUP and scoring anything that looks like a tag ("<a", "</em>") or an
# attribute (`href="..."`) as zero, then ends the summary at the first
# `</p>` where the running count reaches 70.
def test_summary_ends_at_the_paragraph_that_reaches_the_limit():
    # Seventy words of plain prose in the first paragraph, no markup in it
    # at all: the count reaches exactly 70 there and the summary is that
    # paragraph, even though a second one follows.
    post = parse_post(Path("content/posts/elm-minor-imports-syntax-tweak.md"))
    text = summary(post.body)
    assert len(text.split()) == 70
    assert text.endswith("I still think my minor syntax tweak should be adopted.")

def test_a_links_words_count_like_any_others():
    # Structurally the same post as above -- a first paragraph of exactly 70
    # prose words -- but seven of them sit inside a link. Hugo scored `<a`
    # and `href="..."` as zero and let the attribute swallow the word beside
    # it, making the paragraph worth 63 and running the summary on into the
    # second one. A word is a word now, wherever it sits.
    post = parse_post(Path("content/posts/link-python-constant-weirdness.md"))
    text = summary(post.body)
    assert len(text.split()) == 70
    assert text.endswith("the differences are likely an historical anomaly.")

def test_summary_runs_on_to_the_paragraph_after_a_code_block():
    # The limit falls inside a code block, which cannot end a summary --
    # only a `</p>` can -- so it runs on to the end of the next paragraph.
    # This is the one part of the old rule that survives; what changed is
    # that the block's own per-line <span> markup no longer counts as
    # words, so the cut lands sooner.
    post = parse_post(Path("content/posts/minor-refactorings.md"))
    text = summary(post.body)
    assert len(text.split()) == 72
    assert text.endswith("we can re-write the above code as:")

def test_summary_can_end_inside_a_blockquote():
    # The `</p>` that ends the summary is the one nested inside a
    # blockquote, so Hugo's summary is not even well-formed HTML: it leaves
    # the <blockquote> open. Reproduced rather than tidied up.
    post = parse_post(Path("content/posts/needless-do-notation.md"))
    body = post.body
    html = extract_summary(render_entities(body))
    assert html.count("<blockquote>") - html.count("</blockquote>") == 1
    assert summary(body).endswith("1 on average!!!. In other cases,")

# `.Plain` and `.WordCount` come from Hugo's tpl.StripHTML, which is not a
# tag stripper with whitespace cleanup bolted on: a "\n" in the source
# becomes a space, only a closing `</p>` (or a `<br>`) becomes a newline,
# and every run of whitespace then collapses to its own FIRST character.
def test_plainify_makes_paragraph_ends_newlines_and_everything_else_spaces():
    assert plainify("<p>one\ntwo</p>\n<p>three</p>\n") == "one two\nthree\n"

def test_plainify_leaves_a_tagless_string_completely_alone():
    assert plainify("a  b\n\nc") == "a  b\n\nc"

def test_word_count_matches_hugos_for_a_real_post():
    # Hugo's own .WordCount for this post is 1242.
    post = parse_post(Path("content/posts/dsls.md"))
    assert word_count(render_entities(post.body)) == 1242

# docs/hugo-quirks.md quirk 1. Hugo decoded entities BEFORE stripping tags,
# so escaped prose that decoded into something tag-shaped was eaten by its
# tag stripper. We strip first and decode after, which cannot lose text.
def test_plain_keeps_escaped_text_that_would_decode_into_a_tag():
    # This post has a code block containing a literal "<all source files>",
    # rendered as "&lt;all source files&gt;". Decoding first made Hugo read
    # it as a tag and drop it from its own articleBody.
    post = parse_post(Path("content/posts/dsls.md"))
    assert "<all source files>" in plain(render_entities(post.body))

def test_plain_does_not_give_up_partway_through_the_document():
    # An Apache "<Directory ...>" block decoded into an attribute-like token
    # that put Go's stripper into its error state, after which it emitted
    # nothing at all -- silently truncating most of this article. The last
    # paragraph must survive.
    post = parse_post(Path("content/posts/setting-up-nextcloud.md"))
    text = plain(render_entities(post.body))
    assert "<Directory" in text
    # The article's own closing sentence, well past the block that used to
    # trip the stripper. Hugo's articleBody stopped at roughly 1377 chars.
    assert text.rstrip().endswith(
        "This just redirects all incoming http traffic to https.")

# A `dead:` link marks prose whose target no longer exists. The rendered
# element is an <a> with NO href -- the HTML spec's "placeholder for where a
# link might otherwise have been placed" -- so a reader is never offered a
# link they cannot follow, and assistive technology does not announce one.
def test_dead_link_renders_without_an_href():
    out = render("an [excellent post](dead:http://gone.example/p) here")
    assert '<a class="dead-link"' in out
    assert "href" not in out
    assert "excellent post</a>" in out

def test_dead_link_keeps_the_original_url_in_the_tooltip():
    out = render("[x](dead:http://gone.example/a/b?c=1)")
    assert 'title="Link no longer available: http://gone.example/a/b?c=1"' in out

def test_a_normal_link_is_untouched_by_the_dead_link_rule():
    assert render("a [live](https://example.com/p) post") == (
        '<p>a <a href="https://example.com/p">live</a> post</p>\n')

def test_an_autolink_is_untouched_by_the_dead_link_rule():
    out = render("see https://example.com/x for more")
    assert '<a href="https://example.com/x">https://example.com/x</a>' in out

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


# A fence's language can be absent, known, or named but unknown to Pygments,
# and Hugo renders all three differently. `highlight()` returning None means
# the first of those, NOT "could not highlight" -- the two-case reading is
# what a future reader will expect, so pin all three.
def test_unlabelled_fence_gets_hugos_bare_pre():
    out = render("```\nplain text\n```")
    assert '<pre tabindex="0"><code>plain text\n</code></pre>' in out
    assert "highlight" not in out          # no wrapper div, no styling
    assert "language-" not in out

def test_known_language_is_highlighted_inside_the_wrapper():
    out = render("```python\nif x:\n    pass\n```")
    assert '<div class="highlight">' in out
    assert 'background-color:#272822' in out
    assert '<code class="language-python" data-lang="python">' in out
    assert 'style="color:#66d9ef">if</span>' in out    # a real token span

def test_unknown_language_keeps_the_structure_but_not_the_colouring():
    # Chroma has a MoonBit lexer and Pygments does not. Falling back to the
    # unlabelled form would leave this one block unstyled amongst 500-odd
    # Monokai ones; only the token colouring is accepted drift.
    out = render("```moonbit\nfn f() -> Int { 1 }\n```")
    assert '<div class="highlight">' in out
    assert 'background-color:#272822' in out
    assert '<code class="language-moonbit" data-lang="moonbit">' in out
    assert '<span style="color:#' not in out           # nothing was coloured
    # Chroma still wraps each line whether or not it coloured anything in it.
    assert '<span style="display:flex;"><span>fn f() -&gt; Int { 1 }\n' in out
