import contextlib
import os
import pathlib
import subprocess
import sys

import black as blk
import git
import isort
import pkg_resources
import yaml
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter

import versioneer

from .errors import OutputDirExistsError, RenderError


def render(plugin_metadata, output, template=None, clobber=False):
    if template is None:
        template = pkg_resources.resource_filename("babelizer", "data")

    try:
        path = render_plugin_repo(
            template,
            context=plugin_metadata.as_cookiecutter_context(),
            output_dir=output,
            clobber=clobber,
        )
    except OutputDirExistsException as err:
        raise OutputDirExistsError(", ".join(err.args))

    with open(path / "babel.yaml", "w") as fp:
        plugin_metadata.dump(fp)

    install_versioneer(path)
    prettify_python(path)

    return path.resolve()


def render_plugin_repo(template, context=None, output_dir=".", clobber=False):
    """Render a repository for a pymt plugin.

    Parameters
    ----------
    template: bool
        Path (or URL) to the cookiecutter template to use.
    context: dict, optional
        Context for the new repository.
    output_dir : str, optional
        Name of the folder that will be the new repository.
    clobber: bool, optional
        If a like-named repository already exists, overwrite it.

    Returns
    -------
    path
        Absolute path to the newly-created repository.
    """
    output_dir = pathlib.Path(output_dir)
    context = context or {}

    try:
        cookiecutter(
            template,
            extra_context=context,
            output_dir=output_dir,
            no_input=True,
            overwrite_if_exists=clobber,
        )
    except OutputDirExistsException as err:
        raise OutputDirExistsError(", ".join(err.args))

    name = context["plugin_name"]

    # path = os.path.join(output_dir, "pymt_{}".format(context["plugin_name"]))
    # if not os.path.isdir(path):
    path = output_dir / f"pymt_{name}"
    if not path.is_dir():
        raise RenderError("error creating {0}".format(path))

    git.Repo.init(output_dir)

    return path


@contextlib.contextmanager
def as_cwd(path):
    prev_cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prev_cwd)


def install_versioneer(path_to_package):
    with as_cwd(path_to_package):
        subprocess.call(["versioneer", "install"])


def blacken_file(filepath):
    with open(filepath, "r") as fp:
        try:
            new_contents = blk.format_file_contents(
                fp.read(), fast=True, mode=blk.FileMode()
            )
        except blk.NothingChanged:
            new_contents = None
    if new_contents:
        with open(filepath, "w") as fp:
            fp.write(new_contents)


def prettify_python(path_to_repo):
    path_to_repo = pathlib.Path(path_to_repo)
    with open(path_to_repo / "babel.yaml") as fp:
        meta = yaml.safe_load(fp)
    module_name = "pymt_" + meta["plugin"]["name"]

    files_to_fix = [
        path_to_repo / "setup.py",
        path_to_repo / module_name / "bmi.py",
        path_to_repo / module_name / "__init__.py",
    ]

    config = isort.Config(quiet=True)
    for file_to_fix in files_to_fix:
        isort.api.sort_file(file_to_fix, config=config)
        blacken_file(file_to_fix)