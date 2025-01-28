import re
import json

class ArrayAccess:
    def __init__(self, line_identifier, loop_order, lhs, rhs):
        self.line_identifier = line_identifier
        self.loop_order = loop_order
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f"ArrayAccess(line_identifier={self.line_identifier}, loop_order={self.loop_order}, lhs={self.lhs}, rhs={self.rhs})"

def parse_access(line):
    match = re.match(r'([\w%]+)\((.*)\)', line)
    if match:
        array_name = match.group(1)
        access_terms = split_access_terms(match.group(2))
        indirect = any(re.match(r'\w+\(.*\)', term) for term in access_terms)
        return array_name, access_terms, indirect
    return line, [], False

def split_access_terms(terms):
    # Split terms by commas that are not within parentheses
    result = []
    current_term = []
    paren_count = 0
    for char in terms:
        if char == ',' and paren_count == 0:
            result.append(''.join(current_term).strip())
            current_term = []
        else:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            current_term.append(char)
    result.append(''.join(current_term).strip())
    return result

def parse_markdown(content):
    start_index = content.find("START")
    stop_index = content.find("STOP")

    if start_index == -1 or stop_index == -1:
        raise ValueError("Content must contain both 'START' and 'STOP' markers.")

    content = content[start_index + len("START"):stop_index].strip()
    blocks = content.split('\n\n')
    array_accesses = []

    for block in blocks:
        lines = block.strip().split('\n')
        line_identifier = lines[0].strip()
        loop_order = lines[1].strip()
        lhs = []
        rhs = []
        section = None
        for line in lines[2:]:
            if line.strip() == 'lhs':
                section = 'lhs'
                continue
            elif line.strip() == 'rhs':
                section = 'rhs'
                continue
            if re.match(r'[\w%]+\(', line.strip()):
                array_name, access_terms, indirect = parse_access(line.strip())
                access = {
                    'array_name': array_name,
                    'access_terms': access_terms,
                    'indirect': indirect
                }
                if section == 'lhs':
                    lhs.append(access)
                elif section == 'rhs':
                    rhs.append(access)

        array_accesses.append(ArrayAccess(line_identifier, loop_order, lhs, rhs))

    return array_accesses

def main():
    with open("icon_notes.md", "r") as file:
        content = file.read()

    array_accesses = parse_markdown(content)
    for access in array_accesses:
        print(access)

    array_accesses = parse_markdown(content)
    print(json.dumps([access.__dict__ for access in array_accesses], indent=4))

if __name__ == "__main__":
    main()