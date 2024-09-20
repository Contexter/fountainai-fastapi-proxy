# app/utils/file_utils.py
# Utility file for processing file content in chunks.

def process_chunk(chunk, carry_over):
    content = carry_over + chunk.decode("utf-8")
    lines = content.splitlines(keepends=True)

    if not content.endswith("\n"):
        carry_over = lines.pop()
    else:
        carry_over = ""

    return lines, carry_over
