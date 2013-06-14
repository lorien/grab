"""
Facebook last name list converter
"""

def parse_line(line):
	line = line.strip()
	counter, lname = line.split(' ', 1)
	if int(counter) > 300:
		return lname.capitalize()
	else:
		return None


with open('common.txt', 'r') as f:
	lines = f.readlines()

print(len(lines))
data = [_f for _f in [parse_line(line) for line in lines] if _f]
print(len(data))

with open('result.txt', 'w') as f:
	f.write('lname\n')
	for item in data:
		f.write('%s\n' % item)
