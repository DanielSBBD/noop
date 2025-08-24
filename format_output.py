import json
import sys

input = sys.stdin.read()

import re
def decode_escaped_unicode(text):
    # Replace all occurrences of \xHH with the corresponding byte, then decode as utf-8
    def decode_match(match):
        # Get all \xHH sequences in the match
        bytes_seq = bytes([int(b, 16) for b in re.findall(r'\\\\x([0-9a-fA-F]{2})', match.group(0))])
        try:
            return bytes_seq.decode('utf-8')
        except UnicodeDecodeError:
            return match.group(0)  # fallback to original if decode fails
    # Replace all consecutive \xHH sequences
    return re.sub(r'(?:\\\\x[0-9a-fA-F]{2})+', decode_match, text)

input = input[input.find("\\\"text\\\": \\\"")+12:]
input = input.replace("\n", "")
input = input.replace("\'\",    \"b\'", "")
input = input.replace("\\\\\\\\n", "\n")
input = input.replace("\\'", "'")
input = decode_escaped_unicode(input)
input = input[:input.find("\\\"}]")]

print(input)