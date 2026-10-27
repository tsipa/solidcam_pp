"""In-memory model of SolidCAM open/close/copy/delete output directives.

No filesystem access. Nested open/close is modeled as a stack; this assumption
still needs verification against SolidCAM when buffering Multiple_Fixtures.
"""
import re


def assemble_files(text):
    files, main, stack = {}, [], []
    for line in text.splitlines(keepends=True):
        match = re.fullmatch(r'!!(open|close|copy|delete) file=(.+?)!!', line.strip())
        target = files[stack[-1]] if stack else main
        if not match:
            target.append(line)
            continue
        action, name = match.groups()
        if action == 'open':
            if name in files:
                raise AssertionError(f'file already opened: {name}')
            files[name] = []
            stack.append(name)
        elif action == 'close':
            if not stack or stack.pop() != name:
                raise AssertionError(f'unbalanced close: {name}')
        elif action == 'copy':
            if name in stack:
                raise AssertionError(f'copy of an open file: {name}')
            target.extend(files[name])
        else:
            if name in stack:
                raise AssertionError(f'delete of an open file: {name}')
            del files[name]
    if stack or files:
        raise AssertionError(f'unclosed or undeleted files: {stack}, {list(files)}')
    return ''.join(main)
