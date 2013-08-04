__author__ = 'craigglennie'

import jinja2

TEMPLATES_DIR = "../templates"

def get_startup_script(template_file, aws_access_key, aws_secret_key, **kwargs):
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('spotmark', '../templates')
    )
    template = env.get_template(template_file)
    kwargs.update({
        "spotmark": {
            "aws_access_key": aws_access_key,
            "aws_secret_key": aws_secret_key
        }
    })
    return template.render(**kwargs)
