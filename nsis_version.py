import subprocess, re, os
from os import path


def nsis_major_version():
    return 3    # todo: extract from history.but

def nsis_minor_version():
    return 11   # todo: extract from history.but

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
        build_number = 0):
    return f"{major_version}.{minor_version}.{revision_number}.{nsis_build_number(build_number)}"


def nsis_packed_version(
        major_version=nsis_major_version(),
        minor_version=nsis_minor_version(),
        revision_number=nsis_revision_number(),
        build_number = 0):
    # instead of '0xMMmmmrrb' we'll use '0xMMmmmbbb'. 'bbb' range is [0, 4095]
    majver = min(major_version, 0xff)
    minver = min(minor_version, 0xfff) 
    buildno = min(nsis_build_number(build_number), 0xfff)
    return '0x%0.2x%0.3x%0.3x' % (majver, minver, buildno)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--build-number", type=int, default=0)
    args = parser.parse_args()
    
    print(f"version={nsis_version(build_number=args.build_number)}")
    print(f"packed_version={nsis_packed_version(build_number=args.build_number)}")
