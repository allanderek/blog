# The dev server

`./debug.sh` builds the site and serves it at <http://localhost:8080>,
rebuilding whenever anything under `content/`, `css/` or `static/` changes.

This document records three problems it had, what caused them, and what was
done about each — mostly so that the reasoning behind the fixes survives, and
so nobody re-introduces the slow version by "simplifying" the caches.

---

## 1. Startup took 20 seconds

**Symptom.** `./debug.sh` printed nothing for about 20 seconds before serving.

**Cause.** Not the size of the site — redundant work. The build rendered the
same markdown over and over: markdown-it's `render` ran **2361 times for 178
posts**. A post is rendered for its own page, again for its JSON-LD, again for
every feed it appears in (72 of them), and again for every listing it appears
on — home, archives, `/posts/`, and one per tag. `render_entities` alone was
83% redundant.

**Fix.** `generator/markdown.py` memoises the four pure functions — `render`,
`render_entities`, `plainify`, `_extract_summary`. They are safe to cache
because they are deterministic: the `Slugger` that assigns heading ids is
built fresh per call.

| | cold build |
|---|---|
| before | 19.1s |
| `render` + `render_entities` | 7.4s |
| all four | **4.5s** |

Output is byte-identical across all 417 files; the only difference between a
before and after build is the Atom feed's own `<updated>` timestamp, which
differs between any two builds anyway.

This is not only a dev-server win. CI, `check-site.sh` and both link checkers
all build the site.

**Why the caches are keyed on the argument string.** Because that makes them
correct by construction: edit a post and its body is a different key, so a
changed file cannot be served a stale render. There is no invalidation logic,
so there is no invalidation logic to get wrong. `tests/test_markdown.py`'s
`test_editing_a_body_cannot_hit_a_stale_cache_entry` pins this.

The obvious "improvement" — keying on a file path so that an edit *replaces*
the old entry instead of accumulating beside it — is a trap twice over. These
functions are called with strings from front matter and the CV as well as post
bodies, so a path is not something every caller could supply; and it would
need real invalidation logic. The cost of content-keying is that an edited
post's old body lingers in the cache, which is why `maxsize` is bounded. That
bound has to stay comfortably above one build's working set (measured:
207/358/686/180 distinct keys) or the build itself starts thrashing.

---

## 2. No rebuild on save

**Symptom.** Seeing an edit meant stopping and restarting the server, paying
the 20 seconds again.

**Fix.** A watcher thread polls `content/`, `css/` and `static/` twice a
second and rebuilds on any change. Polling rather than `watchdog`: a few
hundred `stat` calls twice a second costs nothing next to a 0.4s rebuild, and
it avoids a dependency and its platform quirks.

**Each rebuild is a FULL rebuild into a brand-new directory**, not a patch of
the page you touched. This matters more than it sounds:

`site.build` writes files but never removes them, so rebuilding over the
previous output would leave the page of a post you just *deleted* sitting
there, still being served. An internal link to that post would keep passing
locally while breaking on production, which builds from nothing. Building into
a fresh directory and swapping gives the dev server the same from-blank
semantics as the real build.

That is affordable only because of §1: a warm rebuild takes **0.4s**. The
speed fix is what made the safe design cheap enough to choose.

A failed build does not take the server down — it keeps serving the last good
build and prints the error, so a half-typed front matter block is a message
rather than a broken site.

**`generator/` is watched separately.** Editing the generator cannot be picked
up by a rebuild, because this process already imported the old code; a rebuild
would silently use it. So that case prints a note asking for a restart rather
than pretending to have applied the change.

---

## 3. "Address already in use", with nothing on the port

**Symptom.** Starting the server sometimes failed with `OSError: [Errno 98]
Address already in use` — as a traceback, and *after* it had already printed
`serving ... at http://localhost:8080`. `lsof -i:8080` showed nothing.

**Cause, certain.** The "serving" line was printed *before* the bind, so a
failure looked like a server that had started and then died. A traceback is
also the wrong output for a routine busy port.

**Cause, probable.** The server was `socketserver.TCPServer`, whose
`allow_reuse_address` defaults to `False`. Without `SO_REUSEADDR`, sockets
left in `TIME_WAIT` on the port block a rebind for around a minute after a
Ctrl-C — and a `TIME_WAIT` socket has no owning process, which is exactly why
`lsof` showed nothing. `http.server.HTTPServer` sets `allow_reuse_address =
True` for precisely this reason; `TCPServer` was the one class that does not.

This is a textbook diagnosis that matches the evidence, but it was **not
reproduced on demand** — two attempts closed their connections too cleanly to
leave a socket in `TIME_WAIT`. It is recorded as probable rather than proven.
The fix is standard and harmless either way, and it also covers the other
candidate cause (restarting before the previous process has fully exited).

**Fix.** `http.server.ThreadingHTTPServer`, which sets `allow_reuse_address`
and additionally stops one browser keep-alive connection stalling every other
request. Bind first and announce second, and report a busy port as a message
naming `ss -tlnp` and `--port` rather than as a traceback.

---

## Flags

    ./debug.sh                              # build, serve, watch
    python3 -m generator serve --port 9000  # a different port
    python3 -m generator serve --no-watch   # build once, then just serve
