"""HELP lists every registered command (task #24: commands registered under
an unknown category used to vanish from HELP)."""


def test_every_registered_command_is_in_a_category(basic):
    registry = basic.command_registry
    categorised = {name for names in registry.categories.values() for name in names}
    assert set(registry.commands) <= categorised


def test_help_lists_resume_and_open(basic, helpers):
    text = ' '.join(helpers.get_text_output(basic.process_command('HELP')))
    assert 'RESUME' in text
    assert 'OPEN' in text
