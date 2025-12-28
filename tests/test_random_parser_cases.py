import unittest
from unittest.mock import patch

from sophie_bot.modules.notes.utils.random_parser import parse_random_text


class TestRandomParser(unittest.TestCase):
    def test_no_delimiters(self):
        """Test text without any delimiters."""
        text = "Hello world, how are you?"
        self.assertEqual(parse_random_text(text), text)

    def test_empty_string(self):
        """Test empty string input."""
        self.assertEqual(parse_random_text(""), "")

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_single_choice(self, mock_choice):
        """Test a single choice between options."""
        mock_choice.return_value = "world"
        text = "Hello %%%world%%%universe%%% today!"
        self.assertEqual(parse_random_text(text), "Hello world today!")

        # Verify choice was called with correct options
        mock_choice.assert_called_once_with(["world", "universe"])

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_multiple_choice_sections(self, mock_choice):
        """Test multiple choice sections."""
        mock_choice.side_effect = ["good", "day"]
        text = "Have a %%%good%%%bad%%% %%%day%%%night%%%!"
        self.assertEqual(parse_random_text(text), "Have a good day!")

        # Verify choice was called with correct options
        mock_choice.assert_any_call(["good", "bad"])
        mock_choice.assert_any_call(["day", "night"])

    def test_empty_options(self):
        """Test empty options handling."""
        text = "Hello %%%%%% world"
        self.assertEqual(parse_random_text(text), "Hello  world")

    def test_trailing_delimiter(self):
        """Test text with trailing delimiter."""
        text = "Hello world%%%"
        self.assertEqual(parse_random_text(text), "Hello world")

    def test_leading_delimiter(self):
        """Test text with leading delimiter."""
        text = "%%%Hello%%%Hi%%% world"
        self.assertEqual(parse_random_text(text).strip(), "Hello world" or "Hi world")

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_multiline_options(self, mock_choice):
        """Test multiline options."""
        mock_choice.return_value = "world\nplanet"
        text = """Hello
%%%
world
planet
%%%
universe
galaxy
%%%
"""
        expected = """Hello
world
planet
"""
        self.assertEqual(parse_random_text(text), expected)
        mock_choice.assert_called_once_with(["world\nplanet", "universe\ngalaxy"])

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_multiline_with_multiple_sections(self, mock_choice):
        """Test multiple multiline sections."""
        mock_choice.side_effect = ["morning\n", "world"]
        text = """Good
%%%
morning

%%%
evening

%%%

%%%
world
%%%
universe
%%%"""
        expected = """Good
morning

world"""
        self.assertEqual(parse_random_text(text), expected)

    def test_whitespace_handling(self):
        """Test whitespace handling in options."""
        text = "Hello %%%   world   %%%   universe   %%% today!"
        result = parse_random_text(text)
        self.assertTrue(result in ["Hello    world    today!", "Hello    universe    today!"])

    def test_nested_delimiters_not_supported(self):
        """Test that nested delimiters are not specially handled."""
        text = "Hello %%%world%%%universe%%%nested%%%options%%% today!"
        result = parse_random_text(text)
        # Should treat as alternating normal/choice sections
        possible_results = [
            "Hello world today!",
            "Hello universe today!",
            "Hello nested today!",
            "Hello options today!",
        ]
        self.assertIn(result, possible_results)

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_boundary_by_whitespace_between_sections(self, mock_choice):
        # Two independent sections separated by whitespace-only should both be chosen
        mock_choice.side_effect = ["y", "C"]
        text = "A %%%x%%%y%%%  %%%B%%%C%%%"
        result = parse_random_text(text)
        self.assertEqual(result, "A y  C")

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_empty_option_at_start_of_section(self, mock_choice):
        mock_choice.return_value = "middle"
        text = "Start %%%%%%middle%%% end"
        # Options are ["", "middle"] -> choose "middle"
        self.assertEqual(parse_random_text(text), "Start middle end")
        mock_choice.assert_called_once_with(["", "middle"])

    @patch("sophie_bot.modules.notes.utils.random_parser.choice")
    def test_avoid_triple_newlines_on_multiline_boundaries(self, mock_choice):
        # When a section ends with a newline and the boundary whitespace starts with a newline,
        # the parser normalizes to avoid an extra blank line.
        mock_choice.side_effect = ["line1\n", "beta"]
        text = (
            "Title\n"  # preface
            "%%%\n"  # start section 1
            "line1\n"  # option A (ends with \n)
            "%%%\n"  # delimiter + boundary starts with \n (whitespace-only)
            "%%%beta%%%gamma%%%"  # section 2
        )
        result = parse_random_text(text)
        # Expect exactly one blank line between chosen option and next section result,
        # not two or three.
        expected = "Title\nline1\nbeta"
        self.assertEqual(result, expected)
