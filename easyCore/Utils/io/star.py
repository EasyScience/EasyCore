__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import textwrap
import warnings
from collections import deque, OrderedDict
from typing import List
import re

_MAX_LEN = 70
_MAX_LABEL_LEN = 65


class FakeItem:
    def __init__(self, value: float, error=None, fixed: bool = None):
        self.raw_value = value
        if fixed is not None:
            self.fixed = fixed
            self.error = 0
        if error is not None:
            self.error = error


class ItemHolder:
    def __init__(self, item):

        self.maxlen = _MAX_LEN

        self.value = item.raw_value
        self.fixed = None
        self.error = None
        if hasattr(item, 'fixed'):
            self.fixed = item.fixed
            if item.error != 0:
                self.error = item.error

    def _get_error_digits(self) -> int:
        return len(f'{self.error}'.split('.')[-1])

    def __str__(self) -> str:
        s = "{}"
        v_in = [self.value]
        if self.error is not None:
            digits = self._get_error_digits()
            v_in.append(int(self.error * 10 ** digits))
            s = "{" + f":0.0{digits}f" + "}({})"
        s = s.format(*v_in)
        if self.fixed is not None and not self.fixed and self.error is None:
            s += '()'
        return self._format_field(s)

    def _format_field(self, v):
        v = v.__str__().strip()
        if len(v) > self.maxlen:
            return ';\n' + textwrap.fill(v, self.maxlen) + '\n;'
        # add quotes if necessary
        if v == '':
            return '""'
        if (" " in v or v[0] == "_") \
                and not (v[0] == "'" and v[-1] == "'") \
                and not (v[0] == '"' and v[-1] == '"'):
            if "'" in v:
                q = '"'
            else:
                q = "'"
            v = q + v + q
        return v

    @staticmethod
    def _makeFakeItem(in_string: str) -> FakeItem:
        in_string = in_string.strip()
        fixed = None
        error = None
        tokens = in_string.split('(')
        try:
            value = float(tokens[0])
        except ValueError:
            value = tokens[0]
            return FakeItem(value, error, fixed)
        if len(tokens) > 1:
            fixed = False
            if tokens[1][0] != ')':
                error = (10 ** -(len(f'{tokens[0]}'.split('.')[1]) + len(tokens[1][:-1]) - 1)) * int(tokens[1][:-1])
        return FakeItem(value, error, fixed)

    @classmethod
    def from_string(cls, in_string: str):
        return cls(cls._makeFakeItem(in_string))


class StarEntry(ItemHolder):
    def __init__(self, item, entry_name: str = None, prefix='_'):

        if entry_name is None:
            entry_name = item.name

        if len(entry_name) > _MAX_LABEL_LEN:
            raise AttributeError(f'Max label length is {int(_MAX_LABEL_LEN)}')

        self.name = entry_name
        self.prefix = prefix
        super(StarEntry, self).__init__(item)

    def __str__(self) -> str:
        s = "{}{}   ".format(prefix, self.name) + super(StarEntry, self).__str__()
        return s

    @classmethod
    def from_string(cls, input_str: str, name_conversion: str = None, prefix='_'):
        name, value = input_str.split('   ')
        name = name[len(prefix):]
        if name_conversion:
            name = name_conversion
        return cls(cls._makeFakeItem(value), name)


class StarBase:
    def __init__(self, core, entry_names: List[str] = None, prefix = '_'):

        if not hasattr(core, '__len__'):
            core = [core]
        self.data = core
        if entry_names is None:
            entry_names = [self.data[0]._kwargs[key].name for key in self.data[0]._kwargs.keys()]

        self.prefix = prefix
        self.labels = entry_names
        self.maxlen = _MAX_LEN


class StarSection(StarBase):
    def __str__(self) -> str:
        return self._section_to_string()

    def _section_to_string(self):
        s = ''
        for idx, key in enumerate(self.data[0]._kwargs.keys()):
            s += f'{StarEntry(self.data[0]._kwargs[key], self.labels[idx], prefix=self.prefix)}\n'
        return s

    @classmethod
    def from_string(cls, real_cls, in_string: str, name_conversion: List[str] = None, prefix='_'):
        items = in_string.split('\n')
        entries = []
        pname = {}
        for idx, item in enumerate(items):
            if not item:
                continue
            conv_item = StarEntry.from_string(item, prefix=prefix)
            p_name = conv_item.name
            if name_conversion is not None:
                p_name = name_conversion[idx]
            pname[p_name] = conv_item.value
            entry = {'name':  conv_item.name,
                     'common_name': p_name,
                     'value': conv_item.value,
                     'fixed': conv_item.fixed,
                     'error': conv_item.error}
            entries.append(entry)
        if hasattr(real_cls, 'from_pars'):
            this_converted = real_cls.from_pars(**pname)
        for idx, entry in enumerate(entries):
            if entry['fixed'] is not None:
                this_converted._kwargs[entry['common_name']].fixed = entry['fixed']
            if entry['error'] is not None:
                this_converted._kwargs[entry['common_name']].error = entry['error']
        return this_converted


class StarLoop(StarBase):

    def __str__(self) -> str:
        return self._loop_to_string()

    def _loop_to_string(self):
        s = "loop_"
        for idx, kw in enumerate(self.data[0]._kwargs.keys()):
            label = self.data[0]._kwargs[kw].name
            if self.labels[idx] is not None:
                label = self.labels[idx]
            s += '\n {}'.format(self.prefix) + label
        for item in self.data:
            line = "\n"
            for kw in self.data[0]._kwargs.keys():
                val = str(ItemHolder(item._kwargs[kw]))
                if val[0] == ";":
                    s += line + "\n" + val
                    line = "\n"
                elif len(line) + len(val) + 2 < self.maxlen:
                    line += "  " + val
                else:
                    s += line
                    line = '\n  ' + val
            s += line
        return s

    @classmethod
    def from_string(cls, groupClass, itemClass, in_string: str, name_conversion: List[str] = None, prefix='_'):
        q = cls._process_string(in_string)
        data = OrderedDict()
        loops = []
        while q:
            s = q.popleft()
            # cif keys aren't in quotes, so show up in s[0]
            if s[0] == "_eof":
                break
            if s[0].startswith(prefix):
                try:
                    data[s[0]] = "".join(q.popleft())
                except IndexError:
                    data[s[0]] = ""
            elif s[0].startswith("loop_"):
                columns = []
                items = []
                while q:
                    s = q[0]
                    if s[0].startswith("loop_") or not s[0].startswith(prefix):
                        break
                    columns.append("".join(q.popleft()))
                    data[columns[-1]] = []
                while q:
                    s = q[0]
                    if s[0].startswith("loop_") or s[0].startswith(prefix):
                        break
                    items.append("".join(q.popleft()))
                n = len(items) // len(columns)
                assert len(items) % n == 0
                loops.append(columns)
                for k, v in zip(columns * n, items):
                    data[k].append(v.strip())
            elif "".join(s).strip() != "":
                warnings.warn("Possible issue in cif file"
                              " at line: {}".format("".join(s).strip()))

        data_list = []
        for idx in range(n):
            d = dict.fromkeys([key[len(prefix):] for key in data.keys()])
            pdata = {}
            for idx2, key in enumerate(data.keys()):
                item = ItemHolder.from_string(data[key][idx])
                this_key = key[len(prefix):]
                if name_conversion is not None:
                    this_key = name_conversion[idx2]
                pdata[this_key] = item.value
                d[key] = item
            if hasattr(itemClass, 'from_pars'):
                made_item = itemClass.from_pars(**pdata)
                for idx2, key in enumerate(data.keys()):
                    this_key = key[len(prefix):]
                    if name_conversion is not None:
                        this_key = name_conversion[idx2]
                    this_item = getattr(made_item, this_key)
                    if d[key].fixed is not None:
                        this_item.fixed = d[key].fixed
                    if d[key].error is not None:
                        this_item.error = d[key].error
                data_list.append(made_item)
            else:
                raise AttributeError
        return groupClass(groupClass.__name__, *data_list)

    @classmethod
    def _process_string(cls, string):
        # remove comments
        string = re.sub(r"(\s|^)#.*$", "", string, flags=re.MULTILINE)
        # remove empty lines
        string = re.sub(r"^\s*\n", "", string, flags=re.MULTILINE)
        # remove non_ascii
        # string = remove_non_ascii(string)
        # since line breaks in .cif files are mostly meaningless,
        # break up into a stream of tokens to parse, rejoining multiline
        # strings (between semicolons)
        q = deque()
        multiline = False
        ml = []
        # this regex splits on spaces, except when in quotes.
        # starting quotes must not be preceded by non-whitespace
        # (these get eaten by the first expression)
        # ending quotes must not be followed by non-whitespace
        p = re.compile(r'''([^'"\s][\S]*)|'(.*?)'(?!\S)|"(.*?)"(?!\S)''')
        for l in string.splitlines():
            if multiline:
                if l.startswith(";"):
                    multiline = False
                    q.append(('', '', '', ' '.join(ml)))
                    ml = []
                    l = l[1:].strip()
                else:
                    ml.append(l)
                    continue
            if l.startswith(";"):
                multiline = True
                ml.append(l[1:].strip())
            else:
                for s in p.findall(l):
                    # s is tuple. location of the data in the tuple
                    # depends on whether it was quoted in the input
                    q.append(s)
        return q


class StarHeader:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return 'data_' + self.name

    @classmethod
    def from_string(cls, in_string: str):
        name = in_string.split('data_')[0]
        return cls(name)
