#!/usr/bin/env python3
'''
Copyright © 2023 Kwankyu Lee <ekwankyu@gmail.com>
                 Harald Schilly <harald.schilly@gmail.com>

Prepare SageMath Documentation for publishing to CDN

- copy `$SAGE_ROOT/local/share/doc/sage/html` to `html` directory
- copy `$SAGE_ROOT/local/share/doc/sage/pdf` to `pdf` directory
- create root index file from `$SAGE_ROOT/local/share/doc/sage/index.html`
- create `robots.txt` file
- create minimal `index.html` files in subdirectories
- remove `_static` symbolic links and resolve the links in html files

Note: the script assumes the html and pdf files were built by running doc-html
and doc-pdf targets. e.g. like this:

  $ nice ionice -c 3 sh -c 'make -j2 && make doc-html && make doc-pdf'

'''

import os
import sys
import shutil
import configparser
import logging
import subprocess as sp

from old_versions import OLD_VERSIONS

logging.basicConfig(level="INFO", format="%(message)s")
log = logging.getLogger(__name__)

default_config = {
    'sage_root' : '',
    'show_older_versions' : 'false',
}

config = configparser.ConfigParser(default_config)
if len(sys.argv) > 1 :
    config.read(sys.argv[1])
else :
    config.read('prepare.cfg')

sage_root = config.get('source', 'sage_root')

show_older_versions = config.getboolean('target', 'show_older_versions')

# ---------------------------------------------------------------
# copy `$SAGE_ROOT/local/share/doc/sage/html` to `html` directory
# ---------------------------------------------------------------

log.info('### Copy html documentation')

sp.Popen(f"rsync -rlp --delete {sage_root}/local/share/doc/sage/pdf ./".split(), stdout=sp.PIPE)

# ---------------------------------------------------------------
# copy `$SAGE_ROOT/local/share/doc/sage/pdf` to `pdf` directory
# ---------------------------------------------------------------

log.info('### Copy pdf documentation')

sp.Popen(f"rsync -rlp --delete {sage_root}/local/share/doc/sage/html ./".split(), stdout=sp.PIPE)

# ------------------------------------------------------------------------------
# generate the root index file from `$SAGE_ROOT/local/share/doc/sage/index.html`
# ------------------------------------------------------------------------------

log.info('### Create the root index file')

shutil.copyfile(f'{sage_root}/local/share/doc/sage/index.html', 'index.html')

if show_older_versions:
    lines = []
    with open('index.html', 'r') as file:
        for line in file:
            lines.append(line)
            if not '<h1>' in line:
                continue

            lines.append('<div class="table ov"><div class="row first"><div class="cell">Older versions:</div>\n')
            for ov in OLD_VERSIONS:
                lines.append(f'<div class="cell"><a href="./{ov}/index.html">{ov}</a></div>\n')
            lines.append('</div></div>\n')

    with open('index.html', 'w') as file:
        for line in lines:
            file.write(line)

# --------------------------
# create `robots.txt` file
# --------------------------

log.info('### Create robots.txt file')

ROBOTS_TXT = [
    "User-agent: *",
    "Disallow: /html/*.txt$",
]

if not show_older_versions:
    for ov in OLD_VERSIONS:
        ROBOTS_TXT.append(f"Disallow: /{ov}/")

with open("robots.txt", "w") as index:
    index.write("\n".join(ROBOTS_TXT))

# -------------------------------------------------
# create minimal index.html files in subdirectories
# -------------------------------------------------

log.info('### Create index.html files')

IDX_TOKEN = "<!-- generated by index.py -->"  # to recognize it later on!
import os
from os import walk, sep
from os.path import join

LANG = {
    "en": "English",
    "es": "Spanish",
    "hu": "Hungarian",
    "pt": "Portuguese",
    "de": "German",
    "ru": "Russian",
    "fr": "French",
    "it": "Italian",
    "ca": "Catalan",
    "tr": "Turkish",
    "ja": "Japanese",
}

intro = """\
<!DOCTYPE html>

<!--

DO NOT EDIT THIS PAGE -- AUTOGENERATED VIA index.py

-->

<head>
<title>SageMath Documentation %(path)s</title>
<link rel="stylesheet" href="/html/en/website/_static/sage.css" type="text/css" />
<style>
html {margin: 20px; font-family: sans-serif; font-size: 90%%; }
body { background-color: white; max-width: 1200px; }
h2 { margin: 0;}
a {text-decoration: none;}
a:hover {text-decoration: underline; }
div.table { display: table; }
div.table.ov { margin-bottom: 1rem; }
div.row { display: table-row; }
div.row:hover {background: #eef; }
div.cell { display: table-cell; padding: 0 2em 0.5em 0; line-height: 1.5em;}
div.lang {font-weight: bold; }
div.row.en {border: 1px solid #ccf;}
div.row.last {height: 3em;}
div.entry {margin: 1em 1em 1em 0; display: inline; white-space: nowrap;}
div.entry.lang-en {font-weight: bold;}
</style>
<link rel="shortcut icon" href="/html/en/website/_static/favicon.ico"/>
</head>
<body>
<a href="https://www.sagemath.org/">
<img width="350" alt="SageMath Logo"
style="border-radius: 10px;"
src="https://www.sagemath.org/pix/sage_logo_new_l_hc_edgy-nq8.png"
title="SageMath Mathematical Software">
</a>
"""

for subdir in ["html", "pdf"]:
    for root, path, filenames in walk(subdir + sep):
        # ignore files in _static, ...
        root_dirs = root.split(sep)
        if any(_.startswith("_") for _ in root_dirs):
            continue
        # if there is no index.html file
        idxfn = join(root, "index.html")
        if "index.html" not in filenames or IDX_TOKEN in open(idxfn,
                                                              "r").read():
            # now we have to write our index.html file
            log.info(f"Creating {idxfn}")
            index = [intro % {"path": root}]
            index.append(IDX_TOKEN)
            if len(root_dirs) > 1:
                index.append('<p><a href="%s">Home</a></p>' %
                             '/'.join([".."] * (len(root_dirs) - 1)))
            index.append('<p><a href="../index.html">Parent Directory</a></p>')
            path = list(filter(lambda _: not _.startswith("_"), path))
            if len(path) > 0:
                index.append('<h2>Sub-Directories</h2>')
                for p in sorted(path):
                    is_lang_list = len(root_dirs) == 1 or (
                        len(root_dirs) == 2 and root_dirs[1] == '')
                    name = LANG.get(p, p) if is_lang_list else p
                    index.append('<p><a href="%(p)s/">%(name)s</a></p>' % {
                        "p": p,
                        "name": name
                    })

            def f_op(fn):
                return not (fn == "index.html" or fn.startswith("genindex-")
                            or fn.startswith("."))

            filenames = list(filter(f_op, filenames))
            if len(filenames) > 0:
                index.append('<h2>Documents</h2>')
                for fn in sorted(filenames):
                    index.append('<p><a href="%(fn)s">%(fn)s</a></p>' %
                                 {"fn": fn})
            index.append("</body></html>")
            with open(idxfn, "w") as outidx:
                outidx.write("\n".join(index))

# -------------------------------------------------------------------
# remove `_static` symbolic links and resolve the links in html files
# -------------------------------------------------------------------

log.info('### Remove symlinks to Sphinx _static directories')

def links():
    for d in ['html', 'pdf']:
        ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), d))
        files_cmd = sp.Popen(f"find {ROOT} -type l -name _static".split(), stdout=sp.PIPE)
        for link in files_cmd.stdout:
            yield link

for link in links():
    link = link.decode('utf8').strip()
    path = os.path.dirname(link)
    target = os.readlink(link)

    log.info(f"Removing symbolic link {link}")

    os.unlink(link)

    log.info(f"Resolving _static to {target} in subdirectories")

    os.system(r'find %s -type f -name "*.html" -exec sed -i '' -e "s/_static/%s/" {} \;' % (path, target.replace('/', r'\/')))

log.info('### Done.')
