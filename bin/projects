#! /usr/bin/env python2
"""Script to set up a new project"""

import os
import re
import sys
import argparse
from bdb import BdbQuit


from dotsite.paths import makepath

def start_debugging():
    try:
        import pudb as pdb
    except ImportError:
        import pdb
    pdb.set_trace()


def parse_args():
    """Parse out command line arguments"""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('strings', default=['.'], nargs='*',
                        help='paths to the projects (default .)')
    parser.add_argument('-U', '--Use_debugger', action='store_true',
                        help='Run the script with pdb (or pudb if available)')
    args = parser.parse_args()
    if args.Use_debugger:
        start_debugging()
    return args


def get_path_to_dir(string):
    path = makepath(string)
    if not path.exists():
        path.mkdir()
    return path.directory()


def get_path_to_module():
    return makepath(__file__).directory()


def copy_project(path_to_there):
    def copy_path(path_to_project_file):
        def copy_file(path_to_project_file, path_to_target):
            def copy_text(string):
                regexp = 'projects'
                replacement = new_project_name
                return re.sub(regexp, replacement, string, count=0, flags=0)

            with open(path_to_project_file) as in_stream:
                text = copy_text(in_stream.read())
                with open(path_to_target, 'w') as out_stream:
                    out_stream.write(text)
            print 'vd %s %s' % (path_to_project_file.short_relative_path_from_here(), path_to_target.short_relative_path_from_here())

        def make_target_directory():
            if path_to_target != path_to_project_file:
                target_directory = path_to_target.directory()
                if not target_directory.isdir():
                    path_to_target.parent.makedirs_p()

        relative_path = path_to_projects().short_relative_path_to(path_to_project_file)
        if path_to_project_file.namebase == path_to_projects().namebase:
            target_name = ''.join([
                path_to_there.namebase, path_to_project_file.ext])
            parts = relative_path.split(os.path.sep)[:-1] + [target_name]
            relative_path = os.path.sep.join(parts)
        else:
            target_name = path_to_project_file.namebase
        path_to_target = path_to_there / relative_path
        make_target_directory()
        copy_file(path_to_project_file, path_to_target)

    def path_to_projects():
        path_to_here = get_path_to_module()
        return path_to_here.parent

    def paths_to_project_files():
        ignores = ['.*', '/.*/', '*files.py', 'projects']
        return list(path_to_projects().walkfiles(ignores=ignores))

    path_to_there.assert_isdir()
    new_project_name = path_to_there.namebase
    for path_to_project_file in paths_to_project_files():
        copy_path(path_to_project_file)

def project(args):
    for string in args.strings:
        path = get_path_to_dir(string)
        copy_project(path)


def main():
    """Run the script"""
    try:
        args = parse_args()
        project(args)
    except (SystemExit, BdbQuit):
        pass
    #except Exception, e:
        #print >> sys.stderr, e
        #return not os.EX_OK
    return os.EX_OK


if __name__ == '__main__':
    sys.exit(main())
