import pytest

from wheelgap import cli
from wheelgap.sources import parse_requirements


@pytest.mark.parametrize(
    "option",
    ["-c constraints.txt", "-cconstraints.txt", "--constraint constraints.txt", "--constraint=constraints.txt"],
)
def test_constraints_pin_without_adding_packages(tmp_path, option):
    path = tmp_path / "requirements.txt"
    path.write_text("ranged\n" + option + "\n", encoding="utf-8")
    (tmp_path / "constraints.txt").write_text("ranged==1.9\nonly-constraint==2\n", encoding="utf-8")
    packages = parse_requirements(path).packages
    assert [(p.name, p.version, p.spec) for p in packages] == [("ranged", "1.9", None)]


def test_nested_constraints_combine_ranges_and_preserve_pins(tmp_path):
    directory = tmp_path / "sub"
    directory.mkdir()
    path = tmp_path / "requirements.txt"
    path.write_text("-r sub/more.txt\n-c sub/constraints.txt\n", encoding="utf-8")
    (directory / "more.txt").write_text("ranged>=1.5\npinned==3\n", encoding="utf-8")
    (directory / "constraints.txt").write_text("-c nested.txt\npinned==1\n", encoding="utf-8")
    (directory / "nested.txt").write_text(
        "ranged<2 \\\n    --hash=sha256:00  # note\n-c constraints.txt\n", encoding="utf-8"
    )
    ranged, pinned = parse_requirements(path).packages
    assert ranged.spec == "<2,>=1.5"
    assert ranged.version is None
    assert pinned.version == "3"


def test_marker_constraint_is_unknown_instead_of_guessed(tmp_path, fake_pypi, capsys):
    path = tmp_path / "requirements.txt"
    path.write_text("ranged\n-c constraints.txt\n", encoding="utf-8")
    (tmp_path / "constraints.txt").write_text('ranged<2; sys_platform == "win32"\n', encoding="utf-8")
    error = parse_requirements(path).packages[0].error
    assert error is not None
    assert "marker" in error
    assert cli.main([str(path), "-p", "3.13", "-t", "linux-x86_64"]) == 1
    assert "unknown" in capsys.readouterr().out


@pytest.mark.parametrize("constraint", ["ranged==1.9", "ranged<2"])
def test_cli_checks_the_constrained_release(tmp_path, fake_pypi, capsys, constraint):
    path = tmp_path / "requirements.txt"
    path.write_text("ranged\n-c constraints.txt\n", encoding="utf-8")
    (tmp_path / "constraints.txt").write_text(constraint + "\n", encoding="utf-8")
    assert cli.main([str(path), "-p", "3.13", "-t", "linux-x86_64"]) == 1
    output = capsys.readouterr().out
    assert "1.9" in output and "source" in output
