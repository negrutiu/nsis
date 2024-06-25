from os import path
import os, sys, shutil, json
from subprocess import Popen, PIPE
from nsis_version import *

# requirements:
# pacman -S mingw-w64-i686-toolchain
# pacman -S mingw-w64-x86_64-toolchain
# pacman -S libtool autoconf-wrapper automake-wrapper     (cppunit)

def run(args):
    """ Execute subprocess and raise exit code exceptions. """
    print(f">> {args}")
    exitcode = Popen(args).wait()
    if exitcode != 0:
        raise OSError(exitcode, f"subprocess exit code {exitcode}")


def win_to_posix(path):
    """ Convert `C:\\path\\file.ext` -> `/C/path/file.ext` """
    if path[1] == ':':
        return '/' + path.replace(':', '').replace('\\', '/')
    return path

def validate_compatibility_with_htmlhelp(filepath):
    """
    Test if the specified path is compatible with `htmlhelp`.  
    `htmlhelp` fails to read input from subdirectories that start with a dot (e.g. `C:\\dir1\\.dir2\\test.hhp` will fail because of `.dir2`)
    """
    for item in path.normpath(filepath).split(os.sep):
        if item.startswith('.'):
            raise Exception(f'directory "{filepath}" is incompatible with "HTML Help" because "{item}" starts with a dot. "NSIS.chm" will fail to build')

def setup_mingw_environ(arch):
    """
    Based on the target architecture, this function:
    - Looks for `msys2` installation directory and adds it to `PATH`
    - Looks for `mingw-w64` installation directory and adds it to `PATH`

    Returns:
      Dictionary `{"msysdir": str, "mingwdir": str}`
    """
    if os.name != 'nt':
        return None

    if arch == 'x86': bitness = '32'
    if arch == 'amd64': bitness = '64'

    msysdir = None
    for subdir in ['msys64', 'msys2']:
        if path.exists(sh := path.join(os.environ['SystemDrive'] + path.sep, subdir, 'usr', 'bin', 'sh.exe')):
            msysdir = path.join(os.environ['SystemDrive'] + path.sep, subdir)
            break
    if msysdir is None: raise Exception('msys2 not found')
    print(f"-- msysdir = {msysdir}")
    os.environ["PATH"] = path.join(msysdir, 'usr', 'bin') + os.pathsep + os.environ["PATH"]   # i.e r"C:\msys64\usr\bin"

    mingwdir = None
    for subdir in [path.join(msysdir, f'mingw{bitness}'), f'mingw{bitness}']:
        if path.exists(gcc := path.join(os.environ['SystemDrive'] + path.sep, subdir, 'bin', 'gcc.exe')):
            mingwdir = path.join(os.environ['SystemDrive'] + path.sep, subdir)
            break
    if mingwdir is None: raise Exception(f"mingw{bitness} not found")
    print(f"-- mingwdir = {mingwdir}")
    os.environ["PATH"] = path.join(mingwdir, 'bin') + os.pathsep + os.environ["PATH"]     # i.e. r"C:\msys64\mingw32\bin", r"C:\mingw32\bin"

    return {'msysdir': msysdir, 'mingwdir': mingwdir}


def setup_msvc_environ(arch):
    """
    This function:
    - Looks for Visual Studio and adds the location of `vcvarsall.bat` to `PATH`
    - Guesses the platform toolset name (i.e. `v143`, `v142`, etc.)
    - Converts the target arch (x86|amd64) to Visual C++ arch (Win32|x64)

    Returns:
      Dictionary `{"installationPath": str, "platformToolset": str, "archName": str}`
    """
    if os.name != 'nt':
        return None

    if path.exists(vswhere := f"{os.environ.get('PROGRAMFILES(X86)', '*')}\\Microsoft Visual Studio\\Installer\\vswhere.exe"): pass
    elif path.exists(vswhere := f"{os.environ.get('PROGRAMFILES', '*')}\\Microsoft Visual Studio\\Installer\\vswhere.exe"): pass
    else: raise Exception('vswhere.exe not found')

    process = Popen([vswhere, '-latest', '-sort', '-format', 'json'], stdout=PIPE, stderr=PIPE)
    (cout, cerr) = process.communicate()
    process.wait()
    # print(cout.decode('utf-8'))
    jout = json.loads(cout)

    # VC install path
    instPath = jout[0]['installationPath']
    print(f"-- installationPath = {instPath}")
    os.environ["PATH"] = path.join(instPath, 'VC', 'Auxiliary', 'Build') + os.pathsep + os.environ["PATH"]

    # guess the platform toolset version
    toolset = None
    if jout[0]['catalog']['productLineVersion'] == '2022': toolset = 'v143'
    if jout[0]['catalog']['productLineVersion'] == '2019': toolset = 'v142'
    if jout[0]['catalog']['productLineVersion'] == '2017': toolset = 'v141'
    print(f"-- platformToolset = {toolset}")

    # VC platform name
    vsarch = arch
    if vsarch == 'x86': vsarch = 'Win32'
    if vsarch == 'amd64': vsarch = 'x64'

    return {'installationPath': instPath, 'platformToolset': toolset, 'archName': vsarch}


def setup_environ(compiler, arch):
    """ Validate `compiler` and `arch` and set up the environment for them. """
    if compiler == 'mingw': compiler = 'gcc'
    if compiler not in ['gcc', 'msvc']: raise Exception(f"unknown compiler {compiler}")
    if compiler == 'msvc' and os.name != 'nt': raise Exception(f"{compiler} not supported on {os.name}")

    if arch == "Win32": arch = 'x86'
    if arch == 'x64': arch = 'amd64'
    if arch != 'x86' and arch != 'amd64': raise Exception(f"unknown arch {arch}")

    if compiler == 'gcc':
        return [compiler, arch, setup_mingw_environ(arch)]
    elif compiler == 'msvc':
        return [compiler, arch, setup_msvc_environ(arch)]


def git_checkout(url, dir, depth = 1):
    """ Clone or Pull a git repository. """
    curdir = path.curdir
    if path.exists(path.join(dir, '.git')):
        os.chdir(dir)
        run(['git', 'pull'])
    else:
        parentdir = path.dirname(dir)
        os.makedirs(parentdir, exist_ok=True)
        os.chdir(parentdir)
        run(['git', 'clone'] + (['--depth', str(depth)] if depth >= 1 else None) + [url, path.basename(dir)])
    os.chdir(curdir)


def build_zlib(compiler, arch, zlibdir):
    compiler, arch, vars = setup_environ(compiler, arch)
    curdir = path.curdir
    os.chdir(zlibdir)
    if compiler == 'gcc' and os.name == 'nt':
        args = [f'mingw32-make.exe', '-fwin32/Makefile.gcc', f'LOC=-D_WIN32_WINNT=0x0400 -static', 'zlib1.dll']
    elif compiler == 'gcc' and os.name != 'nt':
        prefixes = {'x86': 'i686-w64-mingw32-', 'amd64': 'x86_64-w64-mingw32-'}
        args = ['make', '-fwin32/Makefile.gcc', f'PREFIX={prefixes[arch]}', 'LOC=-D_WIN32_WINNT=0x0400 -static', 'zlib1.dll']
    elif compiler == 'msvc':
        args = [f'cmd.exe', '/c', 'call', "vcvarsall.bat", arch, '&&', 'nmake.exe', '-f', 'win32/Makefile.msc', f'LOC=/MT', 'zlib1.dll', 'zdll.lib']
    run(args)
    os.chdir(curdir)


def build_cppunit(compiler, arch, cppunitdir):
    if path.exists(path.join(cppunitdir, 'bin', 'DllPlugInTester.exe')) or path.exists(path.join(cppunitdir, 'lib', 'DllPlugInTester_dll.exe')):
        print("cppunit already built.")
        return
    compiler, arch, vars = setup_environ(compiler, arch)
    curdir = path.curdir
    os.chdir(cppunitdir)
    if compiler == 'gcc':
        prefix = 'mingw32-' if os.name == 'nt' else ''
        outargs = [
            rf"--prefix={win_to_posix(path.join(cppunitdir, 'installed'))}",
            rf'--libdir={win_to_posix(path.join(cppunitdir, "lib"))}',
            rf"--bindir={win_to_posix(path.join(cppunitdir, 'bin'))}"
            ]
        for args in [
            ['sh', './autogen.sh'],
            ['sh', './configure', f'MAKE={prefix}make'] + outargs + ['LDFLAGS=-static', '--disable-silent-rules', '--disable-dependency-tracking', '--disable-doxygen', '--disable-html-docs', '--disable-latex-docs'],
            [f'{prefix}make'],
            [f'{prefix}make', 'install']
            ]:
            run(args)
    elif compiler == 'msvc':
        args = ['cmd.exe', '/c', 'call', 'vcvarsall.bat', arch, '&&', 'msbuild', '/m', '/t:build', path.join(cppunitdir, 'src', 'CppUnitLibraries2010.sln'), '/p:Configuration=Release', f'/p:Platform={vars["archName"]}', f'/p:PlatformToolset={vars["platformToolset" ]}']
        run(args)
    os.chdir(curdir)


def build_nsis_distro(compiler, arch, build_number, zlibdir, cppunitdir=None, nsislog=True, nsismaxstrlen=4096, actions=['test', 'dist']):
    """
    Build a NSIS distribution package. \n
    `zlib` and `cppunit` must be built as well.
    """
    compiler, arch, vars = setup_environ(compiler, arch)

    if os.name == 'nt':
        if path.exists(help_workshop := path.join(os.environ['PROGRAMFILES(X86)'], 'HTML Help Workshop')):
            os.environ['PATH'] += os.pathsep + help_workshop     # NSIS.chm
            validate_compatibility_with_htmlhelp(path.dirname(__file__))

    args = [f'scons',
            f'TARGET_ARCH={arch}',
            f'ZLIB_W32={zlibdir}',
            f'VERSION={nsis_version(build_number=build_number)}',
            f'VER_MAJOR={nsis_major_version()}',
            f'VER_MINOR={nsis_minor_version()}',
            f'VER_REVISION={nsis_revision_number()}',
            f'VER_BUILD={nsis_build_number(build_number)}',
            f'VER_PACKED={nsis_packed_version(build_number=build_number)}',
            f'DISTNAME=negrutiu-{compiler}',
            f'STRIP=1',
            f'SKIP_UTILS="NSIS Menu"',
            f'NSIS_CONFIG_LOG={"Yes" if nsislog else "No"}',
            f'NSIS_CONFIG_LOG_TIMESTAMP={"Yes" if nsislog else "No"}',
            f'NSIS_MAX_STRLEN={nsismaxstrlen}']

    if compiler == 'gcc' and os.name == 'nt':
        args += ['TOOLSET=gcc,gnulink,mingw']   # use mingw toolset in Windows

    if compiler == 'gcc':
        args += ['APPEND_LINKFLAGS=-static']

    if cppunitdir is not None and 'test' in actions:
        args += [f'APPEND_CPPPATH={path.join(cppunitdir, "include")}',
                 f'APPEND_LIBPATH={path.join(cppunitdir, "lib")}']

    args += actions

    run(args)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument_group('build')
    parser.add_argument("-a", "--arch", type=str, default='x86', help='Output architecture (x86|amd64)')
    parser.add_argument("-b", "--build-number", type=int, default=0, help='NSIS build number')
    parser.add_argument("-c", "--compiler", type=str, default='gcc', help="Compiler (gcc|msvc)")
    parser.add_argument("-l", "--nsis-log", type=bool, default=True, help='Enable NSIS logging. See LogSet and LogText')
    parser.add_argument("-s", "--nsis-max-strlen", type=int, default=4096, help='Sets NSIS maximum string length. See NSIS_MAX_STRLEN')
    parser.add_argument("-t", "--tests", type=bool, default=True, help='Build and run NSIS unit tests')
    args = parser.parse_args()

    separator = ''

    workdir = path.dirname(__file__)
    os.makedirs(workdir, exist_ok=True)
    print(f"workdir = {workdir}")

    zlibdir = path.join(workdir, '.depend', 'zlib')
    print(separator)
    git_checkout('https://github.com/madler/zlib.git', zlibdir)
    print(separator)
    build_zlib(args.compiler, args.arch, zlibdir)

    cppunitdir = None
    if args.tests:
        cppunitdir = path.join(workdir, '.depend', 'cppunit')
        print(separator)
        git_checkout('git://anongit.freedesktop.org/git/libreoffice/cppunit', cppunitdir)
        print(separator)
        build_cppunit(args.compiler, args.arch, cppunitdir)

    print(separator)
    actions = ['test', 'dist'] if args.tests else ['dist']
    build_nsis_distro(args.compiler, args.arch, args.build_number, zlibdir, cppunitdir, args.nsis_log, args.nsis_max_strlen, actions)
