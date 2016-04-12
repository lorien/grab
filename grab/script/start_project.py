import os
import logging
import shutil
import re
from grab.error import GrabError

logger = logging.getLogger('grab.script.start_project')


def setup_arg_parser(parser):
    parser.add_argument('project_name')
    parser.add_argument('--template')


def process_content(content, context):
    for key, value in context.items():
        re_macros = re.compile(r'\{\{\s*%s\s*\}\}' % re.escape(key))
        if re_macros.search(content):
            content = re_macros.sub(value, content)
    return content


def process_file_path(path, context):
    for key, value in context.items():
        path = path.replace(key, value)
    return path


def underscore_to_camelcase(val):
    items = val.lower().split('_')
    return ''.join(x.title() for x in items)


def main(project_name, template, **kwargs):
    cur_dir = os.getcwd()
    project_dir = os.path.join(cur_dir, project_name)

    if template is None:
        grab_root = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__)))
        template_path = os.path.join(grab_root, 'util/default_project')
    else:
        template_path = template

    if os.path.exists(project_dir):
        raise GrabError('Directory %s already exists' % project_dir)
    else:
        logger.debug('Copying %s to %s' % (template_path, project_dir))
        shutil.copytree(template_path, project_dir)

        project_name_camelcase = underscore_to_camelcase(project_name)
        context = {
            'PROJECT_NAME': project_name,
            'PROJECT_NAME_CAMELCASE': project_name_camelcase,
        }
        for base, dir_names, file_names in os.walk(project_dir):
            for file_name in file_names:
                if file_name.endswith('.py'):
                    file_path = os.path.join(base, file_name)
                    content = process_content(open(file_path).read(), context)
                    new_file_path = process_file_path(file_path, context)
                    with open(new_file_path, 'w') as out:
                        out.write(content)

                    if file_path != new_file_path:
                        os.unlink(file_path)
                        print('%s: OK' % new_file_path)
                    else:
                        print('%s: OK' % file_path)
