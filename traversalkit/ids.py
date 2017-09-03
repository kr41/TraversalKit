"""
The module provides most common ID patterns.


..  data:: ANY_ID

    Wildcard matching.  Matches everything: ``.*``

..  data:: DEC_ID

    Matches decimal numbers only: ``^[\d]+$``


..  data:: HEX_ID

    Matches hexadecimal numbers only: ``^[a-f\d]+$``


..  data:: TEXT_ID

    Matches single word: ``^[\w\-]+$``

"""

import re


ANY_ID = re.compile(r'.*')
DEC_ID = re.compile(r'^[\d]+$')
HEX_ID = re.compile(r'^[a-f\d]+$', re.I)
TEXT_ID = re.compile(r'^[\w\-]+$', re.I)
