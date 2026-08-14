from agent_loom.jsonc import loads, strip_comments


def test_strip_line_comments_outside_strings():
    text = '{\n  "version": 1,\n  "hooks": {\n    // "beforeShellExecution": []\n  }\n}\n'
    data = loads(text)
    assert data["version"] == 1
    assert data["hooks"] == {}


def test_does_not_strip_slashes_inside_strings():
    data = loads('{"url": "https://example.test/path"}')
    assert data["url"] == "https://example.test/path"


def test_block_comments():
    data = loads('{"a": 1, /* skip */ "b": 2}')
    assert data == {"a": 1, "b": 2}
    assert "//" not in strip_comments('{"a": 1} // x\n')
