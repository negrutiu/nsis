from os import listdir, path
import os
import re
import zipfile
import shutil
import stat
from subprocess import Popen
from nsis_version import *

def run(args):
    """ Execute subprocess and raise exit code exceptions. """
    print(f">> {args}")
    exitcode = Popen(args).wait()
    if exitcode != 0:
        raise OSError(exitcode, f"subprocess exit code {exitcode}")


def merge_nsis_distros(distro_x86_dir, distro_amd64_dir, windows_x86_dir=None, windows_amd64_dir=None):
    """
    Share files (stubs, plugins, etc.) between x86 and amd64 NSIS distribution directories.

    Arguments:
    - distro_x86_dir:     x86 distribution directory, usually `.instdist-ubuntu-x86`
    - distro_amd64_dir:   amd64 distribution directory, usually `.instdist-ubuntu-amd64`
    - windows_x86_dir:    Windows distribution directory, usually `.instdist-windows-x86`
    - windows_amd64_dir:  Windows distribution directory, usually `.instdist-windows-amd64`
    """

    # copy files
    for srcdir, srcre, dstdir in [
        # copy Bin\makensisw.exe to root
        [path.join(distro_x86_dir, 'Bin'), r'makensisw\.exe', distro_x86_dir],
        [path.join(distro_amd64_dir, 'Bin'), r'makensisw\.exe', distro_amd64_dir],
        # copy missing root *.exe and *.chm from windows to ubuntu
        [windows_x86_dir, r'^.*\.exe$', distro_x86_dir] if windows_x86_dir else [None, None, None],
        [windows_x86_dir, r'^.*\.chm$', distro_x86_dir] if windows_x86_dir else [None, None, None],
        [windows_amd64_dir, r'^.*\.exe$', distro_amd64_dir] if windows_amd64_dir else [None, None, None],
        [windows_amd64_dir, r'^.*\.chm$', distro_amd64_dir] if windows_amd64_dir else [None, None, None],
        # copy missing Bin\*.exe from windows to ubuntu
        [path.join(windows_x86_dir, 'Bin'), r'^.*\.exe$', path.join(distro_x86_dir, 'Bin')] if windows_x86_dir else [None, None, None],
        [path.join(windows_amd64_dir, 'Bin'), r'^.*\.exe$', path.join(distro_amd64_dir, 'Bin')] if windows_amd64_dir else [None, None, None],
        # merge x86 and amd64 plugins
        [path.join(distro_x86_dir, 'Plugins', 'x86-ansi'), r'.*', path.join(distro_amd64_dir, 'Plugins', 'x86-ansi')],
        [path.join(distro_x86_dir, 'Plugins', 'x86-unicode'), r'.*', path.join(distro_amd64_dir, 'Plugins', 'x86-unicode')],
        [path.join(distro_amd64_dir, 'Plugins', 'amd64-unicode'), r'.*', path.join(distro_x86_dir, 'Plugins', 'amd64-unicode')],
        # merge x86 and amd64 stubs
        [path.join(distro_x86_dir, 'Stubs'), r'^.+-x86-ansi$', path.join(distro_amd64_dir, 'Stubs')],
        [path.join(distro_x86_dir, 'Stubs'), r'^.+-x86-unicode$', path.join(distro_amd64_dir, 'Stubs')],
        [path.join(distro_amd64_dir, 'Stubs'), r'^.+-amd64-unicode$', path.join(distro_x86_dir, 'Stubs')],
        # merge x86 and amd64 Bin\RegTool-*.bin
        [path.join(distro_x86_dir, 'Bin'), r'RegTool-x86\.bin', path.join(distro_amd64_dir, 'Bin')],
        [path.join(distro_amd64_dir, 'Bin'), r'RegTool-amd64\.bin', path.join(distro_x86_dir, 'Bin')],
        ]:
        if srcdir is None or srcre is None or dstdir is None:
            continue
        for file in listdir(srcdir):
            srcfile = path.join(srcdir, file)
            dstfile = path.join(dstdir, file)
            if re.match(srcre, file) is not None and path.isfile(srcfile):
                if not path.exists(dstfile):
                    os.makedirs(dstdir, exist_ok=True)
                    print(f"copy2( {srcfile} --> {dstfile} )")
                    shutil.copy2(srcfile, dstfile)


def build_nsis_package(
        artifacts_dir,
        distro_x86_dir='.instdist-ubuntu-x86',
        distro_amd64_dir='.instdist-ubuntu-amd64',
        windows_x86_dir='.instdist-windows-x86',
        windows_amd64_dir='.instdist-windows-amd64'
        ):
    """ Build x86 and amd64 NSIS distribution packages from `GitHub Actions` artifacts. """
    artifacts_dir = path.abspath(artifacts_dir)
    # print(f"-- artifacts_dir = {artifacts_dir}")

    # unzip all files in `artifacts`
    # this step does nothing when running in GitHub workflow, since artifacts are already unzipped
    for file in listdir(artifacts_dir):
        zippath = path.join(artifacts_dir, file)
        if re.match(r'^.*-gcc.zip$', zippath) and path.isfile(zippath):
            unzipdir = path.join(artifacts_dir, path.splitext(zippath)[0])
            if not path.exists(unzipdir):
                print(f"extract( {zippath} --> {unzipdir} )")
                with zipfile.ZipFile(zippath) as zip:
                    zip.extractall(unzipdir)

    # extract the root directory from the inner .zip file (i.e. artifacts-ubuntu-latest-x86-gcc.zip => nsis-0.0.0.0-x86.zip => .\nsis-0.0.0.0 )
    for dir in listdir(artifacts_dir):
        if path.isdir(path.join(artifacts_dir, dir)):

            outdir = None
            for srcre, dstdir in [
                [r'^.+-ubuntu-latest-x86-gcc$',    distro_x86_dir],
                [r'^.+-ubuntu-latest-amd64-gcc$',  distro_amd64_dir],
                [r'^.+-windows-latest-x86-gcc$',   windows_x86_dir],
                [r'^.+-windows-latest-amd64-gcc$', windows_amd64_dir]
                ]:
                if re.match(srcre, dir):
                    outdir = dstdir
                    break
            if outdir is None:
                continue

            for file in listdir(path.join(artifacts_dir, dir)):
                if re.match(r'^nsis-.+\.zip$', file) != None:
                    with zipfile.ZipFile(path.join(artifacts_dir, dir, file)) as zip:
                        print(f"extract( {path.join(artifacts_dir, dir, file)} --> {artifacts_dir} )")
                        with zipfile.ZipFile(path.join(artifacts_dir, dir, file)) as zip:
                            rootdir = zip.filelist[0].filename.split("/")[0]
                            zip.extractall(artifacts_dir)
                            if path.exists(outdir):
                                shutil.rmtree(outdir)
                            print(f"rename( {path.join(artifacts_dir, rootdir)} --> {outdir} )")
                            os.rename(path.join(artifacts_dir, rootdir), outdir)

    # share files between distros
    merge_nsis_distros(distro_x86_dir, distro_amd64_dir, windows_x86_dir, windows_amd64_dir)


def build_nsis_installer(
        distro_dir,
        arch,
        major_version=nsis_major_version(),
        minor_version=nsis_minor_version(),
        revision_number=nsis_revision_number(),
        build_number=0,
        outfile=None,
        verbose_level=4
        ):
    """ Build NSIS installer from an existing distribution package. """
    # hack: set NSISDIR and NSISCONFDIR variables to help makensis find its stuff (headers, stubs) on posix
    distro_dir = path.abspath(distro_dir)

    os.environ['NSISDIR'] = distro_dir
    os.environ['NSISCONFDIR'] = distro_dir

    makensis = path.join(distro_dir, 'makensis.exe' if os.name == 'nt' else 'makensis')      # 'makensis' on posix, 'makensis.exe' on windows
    if os.name == 'posix':
        mode = stat.S_IMODE(os.lstat(makensis).st_mode)
        os.chmod(makensis, mode | stat.S_IXUSR)     # `chmod u+x makensis`

    args = [
        makensis,
        f'-DOUTFILE={outfile if outfile is not None else path.join(distro_dir, f"nsis-{nsis_version(major_version, minor_version, revision_number, build_number)}-negrutiu-{arch}.exe")}',
        f'-DVERSION={nsis_version(major_version, minor_version, revision_number, build_number)}',
        f'-DVER_MAJOR={major_version}',
        f'-DVER_MINOR={minor_version}',
        f'-DVER_REVISION={revision_number}',
        f'-DVER_BUILD={nsis_build_number(build_number)}',
        r'-DLINK_INFO=https://github.com/negrutiu/nsis',
        r'-DVER_PRODUCTNAME=Unofficial NSIS fork by Marius Negrutiu',
        r'-DVER_LEGALTRADEMARKS=https://github.com/negrutiu/nsis',
        r'-DEXTRA_WELCOME_TEXT=$\r$\n$\r$\n$\r$\n(*) This is an unofficial fork from https://github.com/negrutiu/nsis$\r$\n',
        f'-V{verbose_level}',
        path.join(distro_dir, 'Examples', 'makensis-fork.nsi')
    ]
    run(args)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-a", "--artifacts-dir", type=str, default='artifacts')
    parser.add_argument("-b", "--build-number", type=int, default=0)
    args = parser.parse_args()

    build_nsis_package(args.artifacts_dir)

    for arch in ['x86', 'amd64']:
        print("\n--------------------------------------------------------------------------------\n")
        build_nsis_installer(f'.instdist-ubuntu-{arch}', arch, build_number=args.build_number, verbose_level=3)
