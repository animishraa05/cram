"""Tests for srs.templates — markdown note templates."""

from srs.templates import concept_template, problem_template, sanitize_filename


def test_sanitize_filename_simple():
    assert sanitize_filename("Two Sum") == "two-sum"


def test_sanitize_filename_special_chars():
    result = sanitize_filename("Hello/World:Test?*")
    assert "/" not in result
    assert ":" not in result
    assert "?" not in result
    assert "*" not in result


def test_sanitize_filename_spaces():
    assert sanitize_filename("hello world") == "hello-world"


def test_sanitize_filename_lowercase():
    result = sanitize_filename("Hello World")
    assert result == "hello-world"


def test_problem_template_contains_title():
    t = problem_template("Two Sum", "https://leetcode.com/two-sum/", "Array")
    assert "Two Sum" in t
    assert "https://leetcode.com/two-sum/" in t
    assert "Array" in t


def test_problem_template_has_sections():
    t = problem_template("Test", "", "")
    assert "Approach" in t
    assert "Code" in t
    assert "Complexity" in t


def test_concept_template_contains_title():
    t = concept_template("TCP", "Networking")
    assert "TCP" in t
    assert "Networking" in t


def test_concept_template_has_sections():
    t = concept_template("Test", "Subject")
    assert "What is it" in t
    assert "Intuition" in t
    assert "How it works" in t


def test_problem_template_empty_link():
    t = problem_template("Test", "", "Topic")
    assert "Topic" in t


def test_concept_template_minimal():
    t = concept_template("Title", "Subject")
    assert len(t) > 100  # Should be a substantial template
