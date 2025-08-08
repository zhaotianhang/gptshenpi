import pytest

from notifications import reset, sent_notifications
from workflow import WorkflowInstance, WorkflowTemplate


def build_workflow():
    tpl = WorkflowTemplate()
    tpl.add_approval('a1', approvers=[1], delegates=[2], next='a2')
    tpl.add_approval('a2', approvers=[3])
    return tpl.to_workflow()


def test_execution_flow():
    reset()
    wf = build_workflow()
    inst = WorkflowInstance(wf)
    # initial notification to first approver
    assert sent_notifications[0]['recipient_id'] == 1
    assert inst.current_id == 'a1'
    # flow state shows first node in progress, second pending
    state = inst.flow_state()
    assert state[0]['status'] == 'in_progress'
    assert state[1]['status'] == 'pending'

    inst.act(actor_id=1, result='approved', comments='ok', attachments=['f'])
    assert inst.current_id == 'a2'
    # notification sent to next approver
    assert sent_notifications[-1]['recipient_id'] == 3

    inst.act(actor_id=3, result='approved')
    assert inst.status == 'approved'
    assert inst.current_id is None
    assert len(inst.records) == 2
    assert inst.records[0].attachments == ['f']
    # final flow state shows all approved
    assert all(s['status'] == 'approved' for s in inst.flow_state())


def test_rejection_stops_flow():
    reset()
    wf = build_workflow()
    inst = WorkflowInstance(wf)
    inst.act(actor_id=1, result='rejected', comments='no')
    assert inst.status == 'rejected'
    assert inst.current_id is None
    # one notification to next approver and initial start = 2 total
    assert len(sent_notifications) == 2
