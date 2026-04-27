import dataclasses
import json

import numpy as np
import pytest

from rawfilereader_cli.serialization import to_json, emit_json


@dataclasses.dataclass
class _Nested:
    value: float = 1.0


@dataclasses.dataclass
class _DC:
    name: str = "x"
    arr: object = None
    nested: _Nested = dataclasses.field(default_factory=_Nested)


def test_plain_dict():
    assert json.loads(to_json({"a": 1})) == {"a": 1}


def test_numpy_array():
    data = {"arr": np.array([1.0, 2.0, 3.0])}
    result = json.loads(to_json(data))
    assert result["arr"] == [1.0, 2.0, 3.0]


def test_numpy_integer():
    data = {"n": np.int64(42)}
    assert json.loads(to_json(data))["n"] == 42


def test_numpy_floating():
    data = {"f": np.float32(3.14)}
    result = json.loads(to_json(data))["f"]
    assert abs(result - 3.14) < 0.01


def test_dataclass_serialization():
    dc = _DC(name="test", arr=np.array([10, 20]))
    result = json.loads(to_json(dc))
    assert result["name"] == "test"
    assert result["arr"] == [10, 20]
    assert result["nested"]["value"] == 1.0


def test_unknown_type_falls_back_to_str():
    class Weird:
        def __str__(self):
            return "weird"
    data = {"w": Weird()}
    assert json.loads(to_json(data))["w"] == "weird"


def test_indent_formatting():
    out = to_json({"a": 1}, indent=2)
    assert "\n" in out


def test_emit_json_prints(capsys):
    emit_json({"x": 99})
    captured = capsys.readouterr()
    assert json.loads(captured.out)["x"] == 99
