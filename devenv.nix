{ pkgs, lib, config, inputs, ... }:
{
  # https://devenv.sh/basics/ to set environment variables is required.

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.fd
    pkgs.sd
    pkgs.lychee   # used by ./check-links-external.sh
    (pkgs.python3.withPackages (ps: [
      ps.markdown-it-py
      ps.mdit-py-plugins
      ps.linkify-it-py
      ps.pygments
      ps.pillow
      ps.pytest
      ps.pypdf          # ./make-cv-pdf.sh's check that the PDF really
                        # contains the expandable sections
    ]))
    pkgs.chromium       # headless, prints /cv/ to static/cv.pdf
  ];

  # See full reference at https://devenv.sh/reference/options/

}
