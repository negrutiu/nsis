import glob, importlib, os, subprocess, sys

scriptdir = os.path.dirname(os.path.abspath(__file__))
modulesdir = os.path.join(scriptdir, 'modules.nogit')        # directory for temporary modules

def import_temp_module(modname):
    """ Import module, installing it to a temporary location if necessary. """
    try:
        globals()[modname] = importlib.import_module(modname)
    except ImportError:
        moduledir = os.path.join(modulesdir, modname)
        if not os.path.exists(moduledir):
            print(f'Install {modname} into temporary directory {moduledir}')
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--index-url", "https://pypi.python.org/simple", "--upgrade", "--target", moduledir, modname])
        print(f'Import "{moduledir}"')
        sys.path.insert(0, moduledir)
        globals()[modname] = importlib.import_module(modname)
        return moduledir
    return None

import_temp_module('lief')

def validate_imports(pefile):
    """ Make sure that a PE file does not import DLLs that are not present in `system32` (e.g. `libwinpthread-1.dll`) """
    # print(f'-- {pefile}')
    problems = 0
    config = lief.PE.ParserConfig()
    config.parse_exports = config.parse_reloc = config.parse_rsrc = config.parse_signature = False
    config.parse_imports = True
    if pe := lief.PE.parse(pefile, config):
        assert isinstance(pe, lief.PE.Binary)
        if pe.has_imports:
            for module in pe.imports:
                if (not os.path.exists(os.path.join(os.environ['SystemRoot'], 'System32', module.name)) and
                    not os.path.exists(os.path.join(os.path.split(pefile)[0], module.name))):
                    problems += 1
                    # print(f'-- {pefile} --> {module.name}')
                    for func in module.entries:
                        if not func.is_ordinal:
                            print(f'-- {pefile} --> {module.name}!{func.name}')
    return problems

def validate_output_dir(dir):
    files = problems = 0
    for pefile in glob.iglob('**/*', root_dir=dir, recursive=True):
        if os.path.isfile(os.path.join(dir, pefile)):
            if ext := os.path.splitext(pefile)[1].lower() in ['.exe', '.dll', '']:
                files += 1
                problems += validate_imports(os.path.join(dir, pefile))
    return (files, problems)


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--dir", type=str, default=None, help='root directory to validate')
    args = parser.parse_args()

    dirs = []
    if args.dir:
        dirs.append(args.dir)
    else:
        for subdir in glob.iglob('*', root_dir=scriptdir, recursive=False):
            subdir = os.path.join(scriptdir, subdir)
            if os.path.isdir(subdir):
                for subsubdir in ['.instdist', '.test']:
                    subsubdir = os.path.join(subdir, subsubdir)
                    if os.path.isdir(subsubdir):
                        dirs.append(subsubdir)

    files = problems = 0
    for dir in dirs:
        print(f'Validate "{dir}"')
        f, p = validate_output_dir(dir)
        files += f
        problems += p
    if problems:
        raise RuntimeError(f'{problems} problematic imports in {files} files')
    else:
        print(f'{problems} problematic imports in {files} files')
    exit(problems)