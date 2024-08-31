from glob import glob
from os import path
import os, sys, shutil
from subprocess import Popen
from threading import Thread

from nsis_build import *
from nsis_package import *

def path_match_re_list(filepath, relist=[]):
    """ Match a file path against a list of regular expressions. Returns `True` if a match is found. """
    for expr in relist:
        if re.match(expr, filepath) is not None:
            return True
    return False

def copy_sources(srcdir, dstdir, verbose=False):
    """ Copy project source files to another directory. """
    incl = [
        r'Contrib.+', r'Docs.+', r'Examples.+', r'Include.+', r'Menu.+', r'SCons.+', r'Scripts.+', r'Source.+',
        r'^nsis_.+\.py$', r'^nsisconf\.nsh$', r'^SCons\S+$', r'^COMPILE$', r'^COPYING$', r'^INSTALL$', r'^README.*$'
        ]
    excl = [r'Contrib\\NScurl\\github.*']

    for file in glob('**', root_dir=srcdir, recursive=True):
        if not path.isfile(file) or not path_match_re_list(file, incl) or path_match_re_list(file, excl):
            continue
        srcfile = path.join(srcdir, file)
        dstfile = path.join(dstdir, file)
        if path.exists(dstfile) and os.stat(srcfile).st_mtime == os.stat(dstdir).st_mtime:
            continue
        if verbose:
            print(f"-- copy( {srcfile} --> {dstfile}")
        if path.exists(dstfile):
            os.remove(dstfile)
        else:
            os.makedirs(path.dirname(dstfile), exist_ok=True)
        shutil.copy2(srcfile, dstfile)

error_count = 0

def build_thread(nsisdir, distrodir, compiler, arch, build_number=0, nsislog=True, nsismaxstrlen=4096, tests=True, new_console=True):
    copy_sources(nsisdir, distrodir)
    args = [sys.executable, path.join(nsisdir, distrodir, 'nsis_build.py'), f'-a={arch}', f'-c={compiler}', f'-b={build_number}', f'-l={nsislog}', f'-s={nsismaxstrlen}', f'-t={tests}']
    exitcode = Popen(args, cwd=distrodir, creationflags=(subprocess.CREATE_NEW_CONSOLE if new_console else 0)).wait()
    print(f"-- {args} returned {exitcode}")
    if exitcode != 0:
        global error_count
        error_count += 1

if __name__ == '__main__':
    def to_bool(str):
        if str.lower() in ['true', 'yes', 'on', '1']: return True
        elif str.lower() in ['false', 'no', 'off', '0']: return False
        return None

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-b", "--build-number", type=int, default=0, help='NSIS build number')
    parser.add_argument("-c", "--compiler", type=str, default='gcc', choices=['gcc', 'msvc'], help="Compiler (gcc|msvc)")
    parser.add_argument("-l", "--nsis-log", type=to_bool, default=True, help='Enable NSIS logging. See LogSet and LogText')
    parser.add_argument("-s", "--nsis-max-strlen", type=int, default=4096, help='Sets NSIS maximum string length. See NSIS_MAX_STRLEN')
    parser.add_argument("-p", "--parallel", type=to_bool, default=True, help='Build x86 and amd64 in parallel. Disable to investigate build errors')
    parser.add_argument("-t", "--tests", type=to_bool, default=True, help='Build and run NSIS unit tests')
    parser.add_argument("-v", "--verbose-level", type=int, default=3, help='makensis.exe verbosity level')
    args = parser.parse_args()

    separator = '\n--------------------------------------------------------------------------------\n'

    nsisdir = path.dirname(__file__)
    distro_x86_dir = path.join(nsisdir, f'build-local-{args.compiler}-x86')
    distro_amd64_dir = path.join(nsisdir, f'build-local-{args.compiler}-amd64')

    threads = [
        Thread(target=build_thread, args=[nsisdir, distro_x86_dir, args.compiler, 'x86', args.build_number, args.nsis_log, args.nsis_max_strlen, args.tests, args.parallel]),
        Thread(target=build_thread, args=[nsisdir, distro_amd64_dir, args.compiler, 'amd64', args.build_number, args.nsis_log, args.nsis_max_strlen, args.tests, args.parallel]),
    ]

    print('building...')
    if args.parallel:
        for th in threads:
            th.start()
        for th in threads:
            th.join()
    else:
        for th in threads:
            th.start()
            th.join()
            if error_count > 0:
                break

    if error_count > 0:
        print(f"{error_count}/{len(threads)} architectures failed to build")
        print("Tip: use --parallel=false argument to build sequentially and print the output to the main console")
        exit(error_count)

    instdist_x86_dir = path.join(distro_x86_dir, '.instdist')
    instdist_amd64_dir = path.join(distro_amd64_dir, '.instdist')

    print(separator)
    merge_nsis_distros(instdist_x86_dir, instdist_amd64_dir)

    print(separator)
    build_nsis_installer(instdist_x86_dir, 'x86', build_number=args.build_number, verbose_level=args.verbose_level)
    print(separator)
    build_nsis_installer(instdist_amd64_dir, 'amd64', build_number=args.build_number, verbose_level=args.verbose_level)

    print(separator)
    print('all done.')
    print(separator)
