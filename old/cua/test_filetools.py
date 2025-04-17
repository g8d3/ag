
import pytest
import os
from cua4_rl import FileTools

def test_filetools_save():
    ft = FileTools()
    content = "def hello():\n    return 'world'"
    filename = "test_file.py"
    output_dir = "test_output"
    result = ft.save(content, filename, output_dir)
    assert result == f"Saved to {output_dir}/{filename}"
    with open(os.path.join(output_dir, filename), 'r') as f:
        assert f.read() == content
    os.remove(os.path.join(output_dir, filename))
    os.rmdir(output_dir)

def test_filetools_read():
    ft = FileTools()
    content = "test content"
    filename = "test_read.txt"
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w') as f:
        f.write(content)
    result = ft.read(filename, output_dir)
    assert result == content
    os.remove(os.path.join(output_dir, filename))
    os.rmdir(output_dir)
