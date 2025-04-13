import os, shutil, glob
import stat

scriptdir = os.path.dirname(os.path.abspath(__file__))

def rmtree_onerror(func, path, excinfo):
    ex = excinfo[1]
    if type(ex) in [FileNotFoundError]:
        return
    elif type(ex) in [PermissionError]:
        # remove read-only files such as `.git\objects\pack\pack-0000000000000000000000000000000000000000.idx`
        os.chmod(path, stat.S_IWRITE)
        print(f'-- {path}: removed read-only attribute')
        func(path)
    else:
        print(f'-- [{type(ex)}] {ex}')

for pattern in [
    # directories
    '.vs',
    '.depend',
    'instdist-*',
    '.scons_temp',
    '.test',
    'build-local*',
    'build',
    os.path.join('**', '__pycache__'),
    # files
    '.sconsign.dblite',
    'config.log'
    ]:
    for name in glob.glob(pattern, root_dir=scriptdir, recursive=True):
        if os.path.isdir(fullname := os.path.join(scriptdir, name)):
            print(f'-- rmtree {name}')
            shutil.rmtree(fullname, onerror=rmtree_onerror)
        else:
            print(f'-- remove {name}')
            os.remove(fullname)
