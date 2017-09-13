import sys
import os
import re
import argparse
from orator.commands.application import application
import sea


class BaseCmd:
    ORATOR_CMD = None

    def __init__(self, app):
        self.app = app
        self.argmap = {}
        self.parser = None
        parts = re.findall('[A-Z][^A-Z]*', self.__class__.__name__)
        self.ORATOR_CMD = ':'.join(parts[1:]).lower()

    def add_parser(self, subparsers):
        self.parser = subparsers.add_parser(self.ORATOR_CMD)
        if hasattr(self, 'add_arguments'):
            self.add_arguments()
        return self.parser

    def get_dbconfig(self):
        dbconfig = os.path.join(
            self.app.root_path, 'configs/{}/orator.py'.format(self.app.env))
        if not os.path.exists(dbconfig):
            dbconfig = os.path.join(
                self.app.root_path, 'configs/default/orator.py')
        return dbconfig

    def add_argument(self, *args, **kwargs):
        arg = self.parser.add_argument(*args, **kwargs)
        self.argmap[arg.dest] = arg.option_strings[-1]
        return arg

    def get_arguments(self, args):
        rv = []
        for k, v in self.argmap.items():
            rv += [v, getattr(args, k)]
        return rv

    def run(self, args, extra=[]):
        sys.argv = ['orator', self.ORATOR_CMD] + \
            self.get_arguments(args) + extra
        return application.run()


class CmdHelp(BaseCmd):

    pass


class CmdList(BaseCmd):

    pass


class BaseExecCmd:
    ARG_CONF = True
    ARG_PATH = 'migrations'

    def add_arguments(self):
        if self.ARG_CONF:
            self.add_argument(
                '-c', '--config', default=self.get_dbconfig(),
                help='The config file path')
        self.add_argument(
            '-p', '--path',
            default=os.path.join(self.app.root_path, 'db', self.ARG_PATH),
            help='The path of migrations files to be executed')


class CmdDbSeed(BaseCmd, BaseExecCmd):
    ARG_PATH = 'seeds'


class CmdMakeMigration(BaseCmd, BaseExecCmd):
    ARG_CONF = False


class CmdMakeSeed(BaseCmd, BaseExecCmd):
    ARG_PATH = 'seeds'


class CmdMigrate(BaseCmd, BaseExecCmd):

    pass


class CmdMigrateReset(BaseCmd, BaseExecCmd):

    pass


class CmdMigrateRollback(BaseCmd, BaseExecCmd):

    pass


class CmdMigrateStatus(BaseCmd, BaseExecCmd):

    pass


def main():
    app = sea.create_app(os.getcwd())
    root = argparse.ArgumentParser('seaorator')
    subparsers = root.add_subparsers()
    for k, v in globals().items():
        if k.startswith('Cmd') and issubclass(v, BaseCmd):
            cmd = v(app)
            cmd.add_parser(subparsers).set_defaults(handler=cmd.run)
    args = sys.argv[1:]
    args, extra = root.parse_known_args(args)
    args.handler(args, extra)
