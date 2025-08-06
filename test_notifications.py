import pytest

from notifications import reset, send, sent_notifications
from workflow import Workflow


def build_workflow():
    steps = [
        {
            'id': 'a1',
            'type': 'approval',
            'approvers': [1],
            'next': 'p1',
        },
        {
            'id': 'p1',
            'type': 'push',
            'push': [9],
            'next': 'a2',
        },
        {
            'id': 'a2',
            'type': 'approval',
            'approvers': [3],
            'next': 'end'
        },
        {
            'id': 'end',
            'type': 'push'
        }
    ]
    return Workflow.from_template(steps)


def test_send_multiple_channels():
    reset()
    send([1], 'hello', channels=['in_app', 'sms', 'third_party'])
    assert {n['channel'] for n in sent_notifications} == {'in_app', 'sms', 'third_party'}
    assert all(n['recipient_id'] == 1 for n in sent_notifications)


def test_workflow_notify_next_targets():
    wf = build_workflow()
    reset()
    wf.notify('a1', 'step done')
    assert {n['recipient_id'] for n in sent_notifications} == {3}
    reset()
    wf.notify('p1', 'pushed')
    assert {n['recipient_id'] for n in sent_notifications} == {9, 3}
