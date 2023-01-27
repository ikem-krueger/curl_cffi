from urllib.request import urlretrieve
import os
import platform
import sys
import shutil
import subprocess

uname = platform.uname()

VERSION="0.5.3"
CURL_VERSION="7.84.0"
CONST_FILE="curl_cffi/_const.py"
if uname.system == "Windows":
    LIBDIR = "./lib"
else:
    LIBDIR="/usr/local/lib"


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))

print("Download firefox certs, see: https://curl.se/docs/caextract.html")
urlretrieve("https://curl.se/ca/cacert.pem", "curl_cffi/cacert.pem", reporthook)


# Download my own build of libcurl-impersonate for M1 Mac
if uname.system == "Darwin" and uname.machine == "arm64":
    url = ""
    filename = "./curl-impersonate.tar.gz"
elif uname.system == "Windows":
    url = f"https://github.com/depler/curl-impersonate-win/releases/download/{CURL_VERSION}/curl-impersonate-win.zip"
    filename = "./curl-impersonate.zip"
else:
    url = f"https://github.com/lwthiker/curl-impersonate/releases/download/v{VERSION}/libcurl-impersonate-v{VERSION}.{uname.machine}-linux-gnu.tar.gz"
    filename = "./curl-impersonate.tar.gz"
if os.path.exists(filename):
    print("libcurl-impersonate already exists")
else:
    print(f"Download libcurl-impersonate-chrome from {url}")
    urlretrieve(url, filename, reporthook)
shutil.unpack_archive(filename, LIBDIR)

# TODO download curl automatically

print("extract consts from curl.h")
with open(CONST_FILE, "w") as f:
    f.write("# This file is automatically generated, do not modify it directly.\n\n")
    f.write("from enum import IntEnum\n\n\n")
    f.write("class CurlOpt(IntEnum):\n")
    cmd = r"""
        echo '#include "curl_cffi/include/curl/curl.h"' | gcc -E - | grep -i "CURLOPT_.\+ =" | sed "s/  CURLOPT_/\t/g" | sed "s/,//g"
    """
    output = subprocess.check_output(cmd, shell=True)
    f.write(output.decode())
    f.write("""
	if locals().get("WRITEDATA"):
		FILE = locals().get("WRITEDATA")
	if locals().get("READDATA"):
		INFILE = locals().get("READDATA")
	if locals().get("HEADERDATA"):
		WRITEHEADER = locals().get("HEADERDATA")\n\n
""")
    f.write("class CurlInfo(IntEnum):\n")
    cmd = r"""
        echo '#include "curl_cffi/include/curl/curl.h"' | gcc -E - | grep -i "CURLINFO_.\+ =" | sed "s/  CURLINFO_/\t/g" | sed "s/,//g"
    """
    output = subprocess.check_output(cmd, shell=True)
    f.write(output.decode())
    f.write("""
	if locals().get("RESPONSE_CODE"):
		HTTP_CODE = locals().get("RESPONSE_CODE")\n
""")
