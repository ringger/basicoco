"""End-to-end tests: drive cli_client.py against a live server with pexpect.

Each test starts a fresh CLI client connected to the session's ``live_server``
(see tests/integration/conftest.py) and asserts on real program output. There
are no blanket ``except`` clauses: a timeout or EOF fails the test with the
client's recent output attached.
"""

import pexpect
import pytest

CONNECT_TIMEOUT = 15
STEP_TIMEOUT = 10
PROMPT = '\r\n> '  # cli_client.py's command prompt


@pytest.fixture
def cli(live_server):
    child = pexpect.spawn(live_server.cli_command(), encoding='utf-8',
                          timeout=STEP_TIMEOUT)
    child.expect('Press Ctrl\\+C to exit', timeout=CONNECT_TIMEOUT)
    child.expect(PROMPT)
    yield child
    child.close(force=True)


def send_and_expect(child, line, pattern, timeout=STEP_TIMEOUT):
    child.sendline(line)
    try:
        child.expect(pattern, timeout=timeout)
    except (pexpect.TIMEOUT, pexpect.EOF) as e:
        pytest.fail(f'After sending {line!r}, expected {pattern!r}; '
                    f'got {type(e).__name__}. Recent output:\n{child.before!r}')


def test_store_and_run_program(cli):
    send_and_expect(cli, '10 PRINT "HELLO WORLD"', PROMPT)
    send_and_expect(cli, 'RUN', 'HELLO WORLD')


def test_clear_statement_does_not_end_program(cli):
    send_and_expect(cli, '10 CLEAR 1000', PROMPT)
    send_and_expect(cli, '20 PRINT "AFTER CLEAR"', PROMPT)
    send_and_expect(cli, 'RUN', 'AFTER CLEAR')


def test_input_round_trip(cli):
    send_and_expect(cli, '10 INPUT "NUMBER";N', PROMPT)
    send_and_expect(cli, '20 PRINT "DOUBLE IS";N*2', PROMPT)
    send_and_expect(cli, 'RUN', 'NUMBER')
    send_and_expect(cli, '21', 'DOUBLE IS 42')


def test_ctrl_c_breaks_immediate_loop_and_cli_survives(cli):
    """#35: Ctrl+C while any command runs sends BREAK; it used to exit the
    CLI unless the command was literally RUN."""
    send_and_expect(cli, 'SAFETY OFF', PROMPT)
    cli.sendline('X=0: WHILE 1: X=X+1: WEND')
    try:
        cli.expect(pexpect.TIMEOUT, timeout=1.5)  # let the loop get going
    except pexpect.EOF:
        pytest.fail(f'CLI exited while the loop ran. Output:\n{cli.before!r}')
    cli.sendintr()
    cli.expect('BREAK', timeout=STEP_TIMEOUT)
    send_and_expect(cli, 'PRINT "STILL HERE"', 'STILL HERE')
    assert cli.isalive()


def test_cls_clears_the_terminal(cli):
    send_and_expect(cli, 'CLS', '\x1b\\[2J')


def test_lunar_lander_plays_to_completion(cli):
    """Load the bundled lunar lander and fly it until the landing report."""
    send_and_expect(cli, 'LOAD "lunar_lander"', PROMPT)
    send_and_expect(cli, 'RUN', 'PRESS ENTER TO START')
    cli.sendline('')

    max_turns = 100
    for _ in range(max_turns):
        index = cli.expect([r'THRUST \(0-30\)\?', r'\*\*\* LANDING REPORT \*\*\*',
                            pexpect.TIMEOUT, pexpect.EOF], timeout=STEP_TIMEOUT)
        if index == 0:
            cli.sendline('5')
        elif index == 1:
            break
        else:
            pytest.fail(f'Game stalled before landing. Recent output:\n{cli.before!r}')
    else:
        pytest.fail(f'No landing report after {max_turns} turns')

    send_and_expect(cli, '', 'PLAY AGAIN')  # flush any pending report output
    send_and_expect(cli, 'N', 'THANKS FOR PLAYING')
