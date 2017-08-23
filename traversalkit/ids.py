import re


ANY_ID = re.compile(r'.*')
DEC_ID = re.compile(r'^[\d]+$')
HEX_ID = re.compile(r'^[a-f\d]+$', re.I)
TEXT_ID = re.compile(r'^[\w\-]+$', re.I)
