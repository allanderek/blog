#!/bin/sh

# The CV's content now lives in content/cv.toml, owned by this repo and
# rendered by the generator -- there is no longer an HTML copy to fetch.
# Only the PDF still comes from the external CV project, until the PDF is
# generated here too.
cp ../cv/cv.pdf static/cv.pdf
