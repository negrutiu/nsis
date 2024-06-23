from os import listdir, path
import os
import re
import zipfile
import shutil

def merge_nsis_distros(distro_x86_dir, distro_amd64_dir, windows_x86_dir=None, windows_amd64_dir=None):
    """Merge together x86 and amd64 build packages to form the final NSIS package.

    NSIS packages (x86 and amd64) are built from the `ubuntu` packages, with
    some extra binaries from `windows` packages.

    Arguments:
    distro_x86_dir: `x86` distribution directory, usually `.instdist-ubuntu-x86`
    distro_amd64_dir: `amd64` distribution directory, usually `.instdist-ubuntu-amd64`
    windows_x86_dir: Optional Windows distro required if `distro_x86_dir` is a Posix distro
    windows_amd64_dir: Optional Windows distro required if `distro_amd64_dir` is a Posix distro
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
        if not srcdir or not srcre or not dstdir:
            continue
        for file in listdir(srcdir):
            srcfile = path.join(srcdir, file)
            dstfile = path.join(dstdir, file)
            if re.match(srcre, file) != None and path.isfile(srcfile):
                if not path.exists(dstfile):
                    os.makedirs(dstdir, exist_ok=True)
                    print(f"copy2( {srcfile} --> {dstfile} )")
                    shutil.copy2(srcfile, dstfile)


def build_nsis_package(
        artifacts_dir,
        distro_x86_dir='.instdist-ubuntu-x86',
        distro_amd64_dir='.instdist-ubuntu-amd64',
        windows_x86_dir = '.instdist-windows-x86',
        windows_amd64_dir = '.instdist-windows-amd64'
        ):
    """Merge together x86 and amd64 build packages to form the final NSIS package.

    NSIS packages (x86 and amd64) are built from the `ubuntu` packages, with
    some additional files from `windows` packages.
    """
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
            if not outdir:
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


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--artifacts-dir", type=str, default='artifacts')
    args = parser.parse_args()
    build_nsis_package(args.artifacts_dir)
