import click
from rawfilereader_cli import __version__
from rawfilereader_cli.commands.file_cmds import file_group
from rawfilereader_cli.commands.scan_cmds import scan_group
from rawfilereader_cli.commands.search_cmds import search_group
from rawfilereader_cli.commands.analyze_cmds import analyze_group


@click.group()
@click.version_option(__version__, "--version")
@click.option("--indent", default=None, type=int, help="JSON indent level (default: compact)")
@click.pass_context
def cli(ctx, indent):
    ctx.ensure_object(dict)
    ctx.obj["indent"] = indent


cli.add_command(file_group, name="file")
cli.add_command(scan_group, name="scan")
cli.add_command(search_group, name="search")
cli.add_command(analyze_group, name="analyze")


if __name__ == "__main__":
    cli()
