import pytest
from ass_tg.entities import ArgEntities

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.MarkdownLinkArgument import MarkdownLinkArgument


class MockMarkdownLinkArgument(MarkdownLinkArgument):
    def needed_type(self):
        return ("test", "test")


@pytest.mark.asyncio
async def test_markdown_link_argument_check_no_entities():
    arg = MockMarkdownLinkArgument()
    text = "[text](data)"
    entities = ArgEntities([])
    # This should probably return True, but we expect it to fail if our analysis is correct
    try:
        result = arg.check(text, entities)
        print(f"Check result: {result}")
    except Exception as e:
        print(f"Check failed with: {type(e).__name__}: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_markdown_link_argument_check_no_entities())
