# Adding a new post

Create the post in content/posts/<unique-name>.md
Copy the meta-tag from another post but make sure you update the publish date.
To deploy just push to the 'main' branch.

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
