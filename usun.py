import regex as re

match = re.match('(.?)(20\d\d)([0-1]\d)([0-3]\d)(.?)([0-2]\d)([0-5]\d)([0-5]\d)(.?)(\d\d\d)', '_20250409_162043_001.')
pass
print(match.group(0))

