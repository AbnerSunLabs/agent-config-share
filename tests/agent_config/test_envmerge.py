from agent_config.envmerge import merge_env_map


def test_keeps_live_literal():
    out = merge_env_map({"K": "sk-live"}, ["K"], "cursor")
    assert out["K"] == "sk-live"


def test_fills_missing_with_cursor_ref():
    out = merge_env_map({}, ["K"], "cursor")
    assert out["K"] == "${env:K}"


def test_rewrites_wrong_ref_name():
    out = merge_env_map({"K": "${env:OLD}"}, ["K"], "cursor")
    assert out["K"] == "${env:K}"
