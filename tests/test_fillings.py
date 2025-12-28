import unittest
from unittest.mock import MagicMock

from aiogram.types import Chat, Message, User

from sophie_bot.modules.notes.utils.fillings import process_fillings


class TestProcessFillings(unittest.TestCase):
    def setUp(self):
        self.chat = MagicMock(spec=Chat)
        self.chat.id = 123456
        self.chat.title = "Test Chat"
        self.chat.username = "test_chat"

        self.message = MagicMock(spec=Message, new_chat_members=MagicMock())
        self.message.chat = self.chat

        self.user = MagicMock(spec=User)
        self.user.id = 78910
        self.user.first_name = "Test"
        self.user.last_name = "User"
        self.additional_fillings = {"custom_key": "custom_value"}

    def test_with_empty_text(self):
        text = ""
        result = process_fillings(text, self.message, self.user, self.additional_fillings)
        self.assertEqual(result, "")

    def test_with_chat_fillings(self):
        text = "Chat ID: {chatid}, Name: {chatname}, Nick: {chatnick}"
        expected = "Chat ID: 123456, Name: Test Chat, Nick: test_chat"
        result = process_fillings(text, self.message, None, None)
        self.assertEqual(result, expected)

    def test_with_user_fillings(self):
        text = "User ID: {id}, First: {first}, Last: {last}, Full: {fullname}, Mention: {mention}"
        expected_start = "User ID: 78910, First: Test, Last: User, Full: Test User, Mention: "
        result = process_fillings(text, self.message, self.user, None)
        self.assertTrue(result.startswith(expected_start))
        self.assertIn(self.user.first_name, result)

    def test_with_custom_fillings(self):
        text = "Custom: {custom_key}"
        expected = "Custom: custom_value"
        result = process_fillings(text, self.message, None, self.additional_fillings)
        self.assertEqual(result, expected)

    def test_combined_fillings(self):
        text = "{chatname} - {first} {last}, {custom_key}. Chat ID: {chatid}, UserID: {id}"
        expected = "Test Chat - Test User, custom_value. Chat ID: 123456, UserID: 78910"
        result = process_fillings(text, self.message, self.user, self.additional_fillings)
        self.assertEqual(result, expected)

    def test_with_missing_custom_key(self):
        text = "Missing: {missing_key}"
        result = process_fillings(text, self.message, self.user, self.additional_fillings)
        self.assertEqual(result, text)


if __name__ == "__main__":
    unittest.main()
