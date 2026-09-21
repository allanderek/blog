# Adding a new post

    ./new-post.sh my-new-post                  # content/posts/my-new-post.md
    ./new-post.sh my-new-post "A better title"

The title defaults to the slug, sentence-cased, and the date is now. The path
is the only thing printed on stdout, so it composes with an editor:

    $EDITOR $(./new-post.sh my-post)           # bash
    e (./new-post.sh my-post)                  # fish

Both of those open the editor on nothing when the command fails -- a rejected
slug prints its complaint to stderr, the substitution comes back empty, and
the editor starts on its welcome screen. Assign first and chain on success
instead, which skips the editor entirely:

    p=$(./new-post.sh my-post) && $EDITOR "$p"           # bash
    set p (./new-post.sh my-post); and e $p              # fish

fish propagates the inner command's exit status through `set`, so `and` sees
the failure. Worth a function in `config.fish`:

    function np
        set -l path (./new-post.sh $argv); or return
        e $path
    end

The slug becomes the post's permanent URL, so anything that is not lowercase
letters, digits and single hyphens is refused rather than quietly rewritten.
An existing file is never overwritten.

To deploy, push to the `main` branch.

# Working on a post

    ./debug.sh                  # serve at localhost:8080, rebuilding on save
    ./run-tests.sh              # the unit tests (a bare `pytest` will not work)

`./debug.sh` watches `content/`, `css/` and `static/`, rebuilds in about half a
second, and keeps serving the last good build if one fails. See
docs/dev-server.md.

Editing `content/cv.toml` or any CSS means `static/cv.pdf` is out of date;
`./check-site.sh` will say so, and `./make-cv-pdf.sh` regenerates it.

# Checking the site

All three scripts build the site into a temporary directory and check that
build, so they test what would actually be deployed. None of them touch
`public/`.

    ./check-site.sh             # the home page, feeds and layout are intact
    ./check-links-internal.sh   # every link to this site resolves to a real page
    ./check-links-external.sh   # every link to someone else's site still answers

`check-links-internal.sh` needs no network and takes a second or two. A failure
is always a real broken link, so it is worth keeping at zero. It also reports
the markdown file each broken link came from.

`check-links-external.sh` needs the network and takes a minute or so. It wraps
`lychee` (provided by `devenv.nix`), and extra arguments are passed straight
through to it. Treat a failure as "go and look" rather than as a build error:
hosts go down, rate-limit, or block anything that is not a browser. Add hosts
that are permanently hostile to link checkers to `.lycheeignore`, but only
after confirming by hand that the link is fine.
