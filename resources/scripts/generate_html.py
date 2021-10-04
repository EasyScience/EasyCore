__author__ = "github.com/wardsimon"
__version__ = "0.0.1"

import os
import sys

tag = "eC_alpha"
if len(sys.argv) > 1:
    tag = sys.argv[1]

whl_dir = "dist"
base_url = f"https://github.com/easyScience/easyCore/releases/download/{tag}/"

file = [file for file in os.listdir(whl_dir) if file.endswith(".whl")][0]

header = "<!DOCTYPE html>\n<html>\n<head>\n<title>Links for easyCore (alpha)</title>\n</head>\n<body>\n<h1>Links for easyCore</h1>"
body = f'<a href="{base_url}{file}" data-requires-python="&gt=3.7,&lt4.0">{file[:-4]}</a><br/>'
footer = "</body>\n</html>"

content = "\n".join([header, body, footer])
with open("index.html", "w") as fid:
    fid.write(content)
