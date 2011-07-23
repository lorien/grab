# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
class Form(object):
    def __init__(self, soup):
        self.soup = soup
        self.parse_form()
        self.parse_fields()

    def parse_form(self):
        self.action = self.soup.get('action')
        self.method = self.soup.get('method').lower()

    def parse_fields(self):
        self.fields = {}
        isfield = lambda x: x.name in ('textarea', 'input', 'select')
        for elem in self.soup.findAll(isfield):
            name = elem.get('name')
            if name:
                if elem.name == 'textarea':
                    value = ''.join(unicode(x) for x in elem.contents)
                    field = {'type': 'textarea',
                             'value': value,
                             'name': name}
                if elem.name == 'input':
                    if elem['type'] in ('text', 'hidden', 'submit', 'reset'):
                        field = {'type': elem['type'],
                                 'value': elem.get('value', ''),
                                 'name': name}
                    if elem['type'] == 'checkbox':
                        field = {'type': 'checkbox',
                                 'value': elem.get('value', ''),
                                 'checked': 'checked' in elem,
                                 'name': name}
                    if elem['type'] == 'radio':
                        if name in self.fields:
                            field = self.fields[name]
                        else:
                            field = {'type': 'radio',
                                     'choices': [],
                                     'name': name,
                                     'value': None}
                        field['choices'].append(elem.get('value', ''))
                        if 'selected' in elem:
                            field['value'] = elem.get('value', '')
                if elem.name == 'select':
                    field = {'type': 'select',
                             'choices': [],
                             'name': name,
                             'value': None}
                    for option in elem.findAll('option'):
                        if option.get('value'):
                            label = ''.join(unicode(x) for x in option.contents)
                            field['choices'].append((option['value'], label))
                            if 'selected' in option:
                                field['value'] = option['value']
            self.fields[name] = field

    def get_data(self):
        return dict((x, y['value']) for x, y in self.fields.items())

    def select_random(key):
        field = self.fields[key]
        if field['type'] in ('radio', 'select'):
            field['value'] = random(field['choices'])

    def fill(key, value):
        self.fields[key]['value'] = value
