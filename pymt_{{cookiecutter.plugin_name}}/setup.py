#! /usr/bin/env python
import os
import sys

{%- if cookiecutter.language == 'c' or cookiecutter.language == 'c++' %}
import numpy as np
{% endif %}
import versioneer
from setuptools import find_packages, setup

from distutils.extension import Extension

try:
    import model_metadata
except ImportError:
    def get_cmdclass(*args, **kwds):
        return kwds.get("cmdclass", None)
    def get_entry_points(*args):
        return None
else:
    from model_metadata.utils import get_cmdclass, get_entry_points


{% if cookiecutter.language == 'c' or cookiecutter.language == 'c++' -%}
import numpy as np


include_dirs = [
    np.get_include(),
    os.path.join(sys.prefix, "include"),
    {%- if cookiecutter.include_dirs -%}
    {%- for dir in cookiecutter.include_dirs.split(',') %}
        "{{ dir|trim }}",{% endfor %}
    {%- endif %}
]


libraries = [
    {%- if cookiecutter.libraries -%}
    {%- for lib in cookiecutter.libraries.split(',') %}
        "{{ lib|trim }}",{% endfor %}
    {%- endif %}
]


library_dirs = [
    {%- if cookiecutter.library_dirs -%}
    {%- for libdir in cookiecutter.library_dirs.split(',') %}
        "{{ libdir|trim }}",{% endfor %}
    {%- endif %}
]


define_macros = [
    {%- if cookiecutter.define_macros -%}
    {%- for item in cookiecutter.define_macros.split(',') %}
    {%- set key_value = item.split('=') %}
        ("{{ key_value[0]|trim }}", "{{ key_value[1]|trim }}"),{% endfor %}
    {%- endif %}
]

undef_macros = [
    {%- if cookiecutter.undef_macros -%}
    {%- for macro in cookiecutter.undef_macros.split(',') %}
        "{{ macro|trim }}",{% endfor %}
    {%- endif %}
]


extra_compile_args = [
    {%- if cookiecutter.extra_compile_args -%}
    {%- for arg in cookiecutter.extra_compile_args.split(',') %}
        "{{ arg|trim }}",{% endfor %}
    {%- endif %}
]


ext_modules = [
{%- for entry_point in cookiecutter.entry_points.split(',') %}
    {%- set pymt_class = entry_point.split('=')[0] -%}
    {%- set bmi_lib, _ = entry_point.split('=')[1].split(":") %}
    Extension(
        "pymt_{{cookiecutter.plugin_name}}.lib.{{ pymt_class|lower }}",
        ["pymt_{{cookiecutter.plugin_name}}/lib/{{ pymt_class|lower }}.pyx"],
        language="{{cookiecutter.language}}",
        include_dirs=include_dirs,
        libraries=libraries + ["{{ bmi_lib }}"],
        library_dirs=library_dirs,
        define_macros=define_macros,
        undef_macros=undef_macros,
        extra_compile_args=extra_compile_args,
    ),
{%- endfor %}
]

{%- endif %}

packages = find_packages()
pymt_components = [
{%- for entry_point in cookiecutter.entry_points.split(',') %}
    {%- set pymt_class = entry_point.split('=')[0] -%}
    {%- set plugin_module, plugin_class = entry_point.split('=')[1].split(':') %}
    (
    {%- if cookiecutter.language == 'c' or cookiecutter.language == 'c++' %}
        "{{ pymt_class }}=pymt_{{cookiecutter.plugin_name}}.lib:{{ pymt_class }}",
    {%- else %}
        "{{ pymt_class }}=pymt_{{cookiecutter.plugin_name}}.bmi:{{ pymt_class }}",
    {%- endif %}
        "meta/{{ pymt_class }}",
    ),
{%- endfor %}
]

setup(
    name="pymt_{{cookiecutter.plugin_name}}",
    author="Eric Hutton",
    description="PyMT plugin {{cookiecutter.plugin_name}}",
    version=versioneer.get_version(),
{%- if cookiecutter.language == 'c' or cookiecutter.language == 'c++' -%}
    setup_requires=["cython"],
    ext_modules=ext_modules,
{%- endif %}
    packages=packages,
    cmdclass=get_cmdclass(pymt_components, cmdclass=versioneer.get_cmdclass()),
    entry_points=get_entry_points(pymt_components),
)
