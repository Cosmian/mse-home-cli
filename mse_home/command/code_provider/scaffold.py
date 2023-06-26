"""mse_home.command.code_provider.scaffold module."""

import os
import shutil
from pathlib import Path

import pkg_resources
from jinja2 import Template
from mse_cli_core.conf import AppConf, AppConfParsingOption

from mse_home.log import LOGGER as LOG
from mse_home.model.package import (
    DEFAULT_CODE_DIR,
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_TEST_DIR,
)


def add_subparser(subparsers):
    """Define the subcommand."""
    parser = subparsers.add_parser(
        "scaffold", help="create a new boilerplate MSE web application"
    )

    parser.add_argument(
        "app_name",
        type=str,
        help="Name of the MSE web application to create",
    )

    parser.set_defaults(func=run)


def run(args) -> None:
    """Run the subcommand."""
    project_dir = Path(os.getcwd()) / args.app_name

    # Copy the template files
    shutil.copytree(
        pkg_resources.resource_filename("mse_home", "template"), project_dir
    )

    template_conf_file = project_dir / "mse.toml.template"
    conf_file = project_dir / DEFAULT_CONFIG_FILENAME

    # Initialize the configuration file
    tm = Template(template_conf_file.read_text())
    content = tm.render(name=args.app_name)
    conf_file.write_text(content)
    template_conf_file.unlink()

    app_conf = AppConf.load(conf_file, option=AppConfParsingOption.SkipCloud)

    # Initialize the python code file
    code_dir = project_dir / DEFAULT_CODE_DIR
    template_code_file = code_dir / (app_conf.python_module + ".py.template")
    code_file = template_code_file.with_suffix("")

    tm = Template(template_code_file.read_text())
    content = tm.render(
        app=app_conf.python_variable,
        healthcheck_endpoint=app_conf.healthcheck_endpoint,
    )
    code_file.write_text(content)
    template_code_file.unlink()

    # Initialize the .mseignore
    ignore_file: Path = code_dir / "dotmseignore"
    ignore_file.rename(code_dir / ".mseignore")

    # Initialize the pytest code files
    pytest_dir = project_dir / DEFAULT_TEST_DIR
    template_pytest_file = pytest_dir / "conftest.py.template"
    pytest_file = template_pytest_file.with_suffix("")

    tm = Template(template_pytest_file.read_text())
    content = tm.render()
    pytest_file.write_text(content)
    template_pytest_file.unlink()

    pytest_dir = project_dir / DEFAULT_TEST_DIR
    template_pytest_file = pytest_dir / "test_app.py.template"
    pytest_file = template_pytest_file.with_suffix("")

    tm = Template(template_pytest_file.read_text())
    content = tm.render(healthcheck_endpoint=app_conf.healthcheck_endpoint)
    pytest_file.write_text(content)
    template_pytest_file.unlink()

    LOG.info(  # type: ignore
        "An example app has been generated in the directory: %s/", args.app_name
    )
    LOG.warning("You can configure your MSE application in: %s", conf_file)
