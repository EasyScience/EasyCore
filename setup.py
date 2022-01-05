# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "easyCore",
    "easyCore.Datasets",
    "easyCore.Elements",
    "easyCore.Elements.Basic",
    "easyCore.Elements.HigherLevel",
    "easyCore.Fitting",
    "easyCore.Objects",
    "easyCore.Symmetry",
    "easyCore.Utils",
    "easyCore.Utils.Hugger",
    "easyCore.Utils.io",
]

package_data = {"": ["*"]}

install_requires = [
    "asteval>=0.9.23,<0.10.0",
    "bumps>=0.8,<0.9",
    "lmfit>=1.0,<2.0",
    "numpy>=1.19,<2.0",
    "pint>=0.17,<0.19",
    "uncertainties>=3.1,<4.0",
    "xarray>=0.16,<0.21",
]

setup_kwargs = {
    "name": "easysciencecore",
    "version": "0.1.0",
    "description": "Generic logic for easyScience libraries",
    "long_description": '# [![License][50]][51] [![Release][32]][33] [![Downloads][70]][71] [![CI Build][20]][21] \n\n[![CodeFactor][83]][84] [![Lines of code][81]](<>) [![Total lines][80]](<>) [![Files][82]](<>)\n\n\n<img height="80"><img src="https://raw.githubusercontent.com/easyScience/easyCore/master/resources/images/ec_logo.svg" height="65">\n\n**easyCore** is the foundation of the *easyScience* universe, providing the building blocks for libraries and applications which aim to make scientific data simulation and analysis easier.\n\n## Install\n\n**easyCore** can be downloaded using pip:\n\n```pip install easysciencecore```\n\nOr direct from the repository:\n\n```pip install https://github.com/easyScience/easyCore```\n\n## Test\n\nAfter installation, launch the test suite:\n\n```python -m pytest```\n\n## Documentation\n\nDocumentation can be found at:\n\n[https://easyScience.github.io/easyCore](https://easyScience.github.io/easyCore)\n\n## Contributing\nWe absolutely welcome contributions. **easyCore** is maintained by the ESS and on a volunteer basis and thus we need to foster a community that can support user questions and develop new features to make this software a useful tool for all users while encouraging every member of the community to share their ideas.\n\n## License\nWhile **easyCore** is under the BSD-3 license, DFO_LS is subject to the GPL license.\n\n<!---CI Build Status--->\n\n[20]: https://github.com/easyScience/easyCore/workflows/CI%20using%20pip/badge.svg\n\n[21]: https://github.com/easyScience/easyCore/actions\n\n\n<!---Release--->\n\n[32]: https://img.shields.io/pypi/v/easyScienceCore.svg\n\n[33]: https://pypi.org/project/easyScienceCore\n\n\n<!---License--->\n\n[50]: https://img.shields.io/github/license/easyScience/easyCore.svg\n\n[51]: https://github.com/easyScience/easyCore/blob/master/LICENSE.md\n\n\n<!---Downloads--->\n\n[70]: https://img.shields.io/pypi/dm/easyScienceCore.svg\n\n[71]: https://pypi.org/project/easyScienceCore\n\n<!---Code statistics--->\n\n[80]: https://tokei.rs/b1/github/easyScience/easyCore\n\n[81]: https://tokei.rs/b1/github/easyScience/easyCore?category=code\n\n[82]: https://tokei.rs/b1/github/easyScience/easyCore?category=files\n\n[83]: https://www.codefactor.io/repository/github/easyscience/easycore/badge\n\n[84]: https://www.codefactor.io/repository/github/easyscience/easycore\n',
    "author": "Simon Ward",
    "author_email": None,
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/easyScience/easyCore",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.7,<4.0",
}


setup(**setup_kwargs)
