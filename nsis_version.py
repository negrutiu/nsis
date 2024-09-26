import subprocess
import re
import os
from os import path

def nsis_version_from_history_but():
    """ Read latest version from `history.but`. Returns `(major, minor)` tuple. """
    with open(path.join(path.dirname(__file__), 'Docs', 'src', 'history.but')) as fin:
        matches = re.findall(r'\\H{v(\d+)\.(\d+)}', fin.read())
        # print(matches)
        return int(matches[0][0]), int(matches[0][1])

def nsis_major_version():
    major, minor = nsis_version_from_history_but()
    return major

def nsis_minor_version():
    major, minor = nsis_version_from_history_but()
    return minor

def nsis_revision_number():
    # git log --grep=git-svn-id: -1
    cwd = os.curdir
    os.chdir(path.dirname(__file__))
    process = subprocess.Popen(['git', 'log', '--grep=git-svn-id:', '-1'], stdout=subprocess.PIPE)
    cout = process.communicate()[0]
    os.chdir(cwd)
    # print(output.decode('utf-8'))

    # extract 7431 from "[...] git-svn-id: https://svn.code.sf.net/p/nsis/code/NSIS/trunk@7431 212acab6-be3b-0410-9dea-997c60f758d6 [...]"
    matches = re.match(r'^.*git-svn-id:.*trunk@(\d+)\s.*$', cout.decode('utf-8'), re.DOTALL)
    if matches is not None:
        return int(matches[1])
    return 0

def nsis_build_number(build_number = 0):
    return build_number


def nsis_version(
        major_version=nsis_major_version(),
        minor_version=nsis_minor_version(),
        revision_number=nsis_revision_number(),
        build_number=0):
    return f"{major_version}.{minor_version}.{revision_number}.{nsis_build_number(build_number)}"


def nsis_packed_version(
        major_version=nsis_major_version(),
        minor_version=nsis_minor_version(),
        revision_number=nsis_revision_number(),
        build_number=0):
    # instead of '0xMMmmmrrb' we'll use '0xMMmmmbbb'. 'bbb' range is [0, 4095]
    majver = min(major_version, 0xff)
    minver = min(minor_version, 0xfff) 
    buildno = min(nsis_build_number(build_number), 0xfff)
    return '0x%0.2x%0.3x%0.3x' % (majver, minver, buildno)


def nsis_distro_name():
    process = subprocess.Popen(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE)
    (cout, cerr) = process.communicate()
    exitcode = process.wait()
    if exitcode != 0:
        raise OSError(exitcode, f"subprocess exit code {exitcode}")

    distro = path.basename(cout.decode('utf-8')).replace('\r', '').replace('\n', '').replace(' ', '_')      # current branch name
    if distro == 'master':
        distro = 'negrutiu'
    return distro

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-b", "--build-number", type=int, default=0)
    args = parser.parse_args()
    
    print(f"version={nsis_version(build_number=args.build_number)}")
    print(f"packed_version={nsis_packed_version(build_number=args.build_number)}")
    print(f"distro_name={nsis_distro_name()}")
