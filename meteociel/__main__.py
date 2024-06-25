"""Load the command line interface."""

import click

from meteociel import cli


@click.group()
def main():
    """Météociel API. Type:

        meteociel [COMMAND] --help

    for more information on COMMAND.
    """


for attrname in dir(cli):
    attr = getattr(cli, attrname)
    if isinstance(attr, click.Command):
        main.add_command(attr)


if __name__ == "__main__":
    main()
