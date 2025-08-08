import pytest

from workflow import Workflow, WorkflowTemplate


def build_workflow():
    steps = [
        {
            'id': 'a1',
            'type': 'approval',
            'approvers': [1],
            'delegates': [2],
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


def test_template_parsing_and_order():
    wf = build_workflow()
    a1 = wf.get_node('a1')
    assert a1.approvers == [1]
    assert a1.delegates == [2]
    assert wf.get_next('a1').id == 'p1'
    assert wf.next_approval('a1').id == 'a2'


def test_conditional_jump():
    steps = [
        {
            'id': 'start',
            'type': 'approval',
            'approvers': [1],
            'conditions': [{'expr': 'amount > 100', 'next': 'audit'}],
            'next': 'end'
        },
        {
            'id': 'audit',
            'type': 'approval',
            'approvers': [2],
            'next': 'end'
        },
        {'id': 'end', 'type': 'push'}
    ]
    wf = Workflow.from_template(steps)
    assert wf.get_next('start', {'amount': 150}).id == 'audit'
    assert wf.get_next('start', {'amount': 50}).id == 'end'


def test_default_push_targets():
    wf = build_workflow()
    assert wf.push_targets('a1') == [3]
    assert set(wf.push_targets('p1')) == {9, 3}


def test_approval_requires_approver():
    steps = [{'id': 'a1', 'type': 'approval'}]
    with pytest.raises(ValueError):
        Workflow.from_template(steps)


def test_template_builder_creates_workflow():
    tpl = WorkflowTemplate()
    tpl.add_approval('a1', approvers=[1], next='a2')
    tpl.add_approval('a2', approvers=[2])
    wf = tpl.to_workflow()
    assert wf.start_id == 'a1'
    assert wf.get_node('a2').approvers == [2]
