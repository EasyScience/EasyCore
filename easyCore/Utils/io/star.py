__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

import textwrap
import warnings
from collections import deque, OrderedDict
from typing import List
import re
import operator
from functools import reduce

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


class FakeCore:
    def __init__(self):
        self._kwargs = {}


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

    def to_fake_item(self):
        return FakeItem(self.value, self.error, self.fixed)


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
        s = "{}{}   ".format(self.prefix, self.name) + super(StarEntry, self).__str__()
        return s

    @classmethod
    def from_string(cls, input_str: str, name_conversion: str = None, prefix='_'):
        name, value = input_str.split('   ')
        name = name[len(prefix):]
        if name_conversion:
            name = name_conversion
        return cls(cls._makeFakeItem(value), name)

    def to_class(self, cls, name_conversion: str = None):
        if name_conversion is None:
            name_conversion = self.name
        if hasattr(cls, 'from_pars'):
            new_obj = cls.from_pars(**{name_conversion: self.value})
        if hasattr(new_obj, 'fixed'):
            if self.fixed is not None:
                new_obj.fixed = self.fixed
        if hasattr(new_obj, 'error'):
            if self.error is not None:
                new_obj.error = self.error
        return new_obj


class StarProcess:
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

    @classmethod
    def _loadBlock(cls, in_string: str, prefix='_'):
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
        return data, loops


class StarBase(StarProcess):
    def __init__(self, core, entry_names: List[str] = None, prefix: str = '_'):

        if not hasattr(core, '__len__'):
            core = [core]
        self.data = core
        if entry_names is None:
            entry_names = [self.data[0]._kwargs[key].name for key in self.data[0]._kwargs.keys()]

        self.prefix = prefix
        self.labels = entry_names
        self.maxlen = _MAX_LEN


class StarCollection(StarProcess):
    def __init__(self, *star_objects):
        self.data = star_objects

    def __str__(self) -> str:
        return '\n\n'.join([str(data) for data in self.data])

    @classmethod
    def from_string(cls, in_string, prefix='_'):

        in_string = '\n'.join([item for item in in_string.split('\n') if item and item[0] != '#'])

        blocks = in_string.split('data_')
        data_blocks = []
        for block in blocks:
            if not block:
                continue
            items = block.split('\n')
            if len(items) == 0:
                continue
            data_block = [StarHeader.from_string('data_' + items[0])]
            data, loops = cls._loadBlock('\n'.join(items[1:]))
            for loop in loops:
                data_block.append(StarLoop.from_data(data, [loop], prefix=prefix))
            flattened_loop = reduce(operator.concat, loops)
            data = {k: data[k] for k in data.keys() if k not in flattened_loop}
            for key in data.keys():
                data_block.append(StarEntry.from_string("{}   {}".format(key, data[key])))
            data_blocks.append(data_block)
        if len(data_blocks) == 1:
            data_blocks = data_blocks[0]
        return data_blocks


class StarSection(StarBase):
    def __str__(self) -> str:
        return self._section_to_string()

    def _section_to_string(self):
        s = ''
        for idx, key in enumerate(self.data[0]._kwargs.keys()):
            s += f'{StarEntry(self.data[0]._kwargs[key], self.labels[idx], prefix=self.prefix)}\n'
        return s

    def to_class(self, cls, name_conversions=None):
        if not hasattr(cls, 'from_pars'):
            raise AttributeError
        if name_conversions is None:
            name_conversions = self.labels
        new_object = cls.from_pars(**{k[0]: self.data[0]._kwargs[k[1]].raw_value for k in name_conversions})
        for key in name_conversions:
            attr = getattr(new_object, key[0])
            if hasattr(self.data[0]._kwargs[key[1]], 'fixed'):
                if self.data[0]._kwargs[key[1]].fixed is not None:
                    attr.fixed = self.data[0]._kwargs[key[1]].fixed
                if self.data[0]._kwargs[key[1]].error is not None:
                    attr.error = self.data[0]._kwargs[key[1]].error
        return new_object

    @classmethod
    def from_string(cls, in_string: str, name_conversion: List[str] = None, prefix='_'):
        items = in_string.split('\n')
        data = [FakeCore()]
        names = []
        for idx, item in enumerate(items):
            if not item:
                continue
            this_name = None
            if name_conversion is not None:
                this_name = name_conversion[idx]
            conv_item = StarEntry.from_string(item, name_conversion=this_name, prefix=prefix)
            names.append(conv_item.name)
            data[0]._kwargs[conv_item.name] = conv_item.to_fake_item()
        return cls(data, entry_names=names, prefix=prefix)

    @classmethod
    def from_StarEntries(cls, star_entries: List[StarEntry], name_conversions: List[str] = None, prefix='_'):
        data = [FakeCore()]
        names = []
        for idx, entry in enumerate(star_entries):
            names.append(entry.name)
            data[0]._kwargs[entry.name] = entry.to_fake_item()
        if name_conversions is None:
            name_conversions = names
        return cls(data, entry_names=name_conversions, prefix=prefix)

    def to_StarEntries(self) -> List[StarEntry]:
        return [StarEntry(self.data[0]._kwargs[key], self.labels[idx], prefix=self.prefix)
                for idx, key in enumerate(self.data[0]._kwargs.keys())]


class StarLoop(StarBase):

    def __str__(self) -> str:
        return self._loop_to_string()

    def _loop_to_string(self):
        s = "loop_"
        if len(self.data) == 0:
            return ''
        for idx, kw in enumerate(self.data[0]._kwargs.keys()):
            label = kw
            if not isinstance(self.data[0]._kwargs[kw], FakeItem):
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
    def from_string(cls, in_string: str, name_conversion: List[str] = None, prefix='_'):
        data, loops = cls._loadBlock(in_string, prefix=prefix)
        return cls.from_data(data, loops, name_conversion, prefix)

    @classmethod
    def from_StarSections(cls, star_sections: List[StarSection], name_conversion: List[str] = None, prefix='_'):
        this_data = [section.data[0] for section in star_sections]
        all_names = star_sections[0].labels
        if name_conversion is not None:
            all_names = name_conversion
        return cls(this_data, all_names, prefix)

    def to_StarSections(self) -> List[StarSection]:
        return [StarSection(section, self.labels, prefix=self.prefix) for section in self.data]

    @classmethod
    def from_data(cls, data: OrderedDict, loops=None, name_conversion: List[str] = None, prefix='_'):
        if loops is None:
            loops = [list(data.keys())]
        if len(loops) > 1:
            raise NotImplementedError
        for loop in loops:
            # How many elements are there?
            len_elements = len(data[loop[0]])
            this_data = []
            all_names = []
            for element_idx in range(len_elements):
                fk = FakeCore()
                for idx2, item in enumerate(loop):
                    this_name = item
                    if this_name[0] == '_':
                        this_name = this_name[1:]
                    if name_conversion is not None:
                        this_name = name_conversion[idx2]
                    if element_idx == 0:
                        all_names.append(this_name)
                    conv_item = StarEntry.from_string("{}{}   {}".format(prefix, this_name, data[item][element_idx]),
                                                      this_name, prefix=prefix)
                    fk._kwargs[conv_item.name] = conv_item.to_fake_item()
                this_data.append(fk)
            return cls(this_data, all_names, prefix=prefix)


    def to_class(self, cls_outer, cls_inner, name_conversions=None):
        if not hasattr(cls_inner, 'from_pars'):
            raise AttributeError
        new_objects = []
        for idx in range(len(self.data)):
            if name_conversions is None:
                name_conversions = [[k, k] for k in self.data[idx]._kwargs.keys()]
            new_object = cls_inner.from_pars(**{k[0]: self.data[idx]._kwargs[k[1]].raw_value for k in name_conversions})
            for key in name_conversions:
                attr = getattr(new_object, key[0])
                if hasattr(self.data[idx]._kwargs[key[1]], 'fixed'):
                    if self.data[idx]._kwargs[key[1]].fixed is not None:
                        attr.fixed = self.data[idx]._kwargs[key[1]].fixed
                    if self.data[idx]._kwargs[key[1]].error is not None:
                        attr.error = self.data[idx]._kwargs[key[1]].error
            new_objects.append(new_object)
        return cls_outer(cls_outer.__name__, *new_objects)


class StarHeader:
    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return 'data_' + self.name

    @classmethod
    def from_string(cls, in_string: str):
        name = in_string.split('data_')[1]
        return cls(name)