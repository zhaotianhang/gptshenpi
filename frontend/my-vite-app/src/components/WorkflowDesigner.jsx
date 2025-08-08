import React, { useState } from 'react';
import { 
  Card, Button, Modal, Form, Input, Select, Space, 
  message, Drawer, Divider, Tag 
} from 'antd';
import {
  PlusOutlined, CheckCircleOutlined, SendOutlined,
  BranchesOutlined, StopOutlined, PlayCircleOutlined
} from '@ant-design/icons';

const { Option } = Select;

const WorkflowDesigner = ({ visible, onClose, onSave, users = [] }) => {
  const [nodes, setNodes] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [form] = Form.useForm();

  const handleAddNode = (type) => {
    const newNode = {
      id: `node_${Date.now()}`,
      name: type === 'approval' ? '审批节点' : '推送节点',
      type: type,
      approvers: [],
      delegates: [],
      pushTargets: []
    };
    setNodes([...nodes, newNode]);
  };

  const handleEditNode = (node) => {
    setEditingNode(node);
    form.setFieldsValue({
      name: node.name,
      approvers: node.approvers || [],
      delegates: node.delegates || [],
      pushTargets: node.pushTargets || []
    });
    setModalVisible(true);
  };

  const handleSaveNode = (values) => {
    const updatedNode = { ...editingNode, ...values };
    const newNodes = nodes.map(node => 
      node.id === editingNode.id ? updatedNode : node
    );
    setNodes(newNodes);
    setModalVisible(false);
    setEditingNode(null);
    form.resetFields();
  };

  const handleSaveWorkflow = () => {
    if (nodes.length === 0) {
      message.error('请至少添加一个节点');
      return;
    }
    onSave({ nodes });
    message.success('流程保存成功');
  };

  return (
    <Drawer
      title="流程设计器"
      width="80%"
      open={visible}
      onClose={onClose}
      extra={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button type="primary" onClick={handleSaveWorkflow}>
            保存流程
          </Button>
        </Space>
      }
    >
      <div style={{ display: 'flex', gap: '16px' }}>
        <div style={{ width: '200px' }}>
          <Card title="节点类型" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                icon={<CheckCircleOutlined />}
                onClick={() => handleAddNode('approval')}
                style={{ width: '100%' }}
              >
                审批节点
              </Button>
              <Button 
                icon={<SendOutlined />}
                onClick={() => handleAddNode('push')}
                style={{ width: '100%' }}
              >
                推送节点
              </Button>
            </Space>
          </Card>
        </div>

        <div style={{ flex: 1 }}>
          <Card title="流程节点" size="small">
            {nodes.map((node, index) => (
              <Card 
                key={node.id} 
                size="small" 
                style={{ marginBottom: '8px' }}
                extra={
                  <Button 
                    size="small" 
                    onClick={() => handleEditNode(node)}
                  >
                    编辑
                  </Button>
                }
              >
                <div>
                  <strong>{node.name}</strong>
                  <Tag color={node.type === 'approval' ? 'blue' : 'purple'}>
                    {node.type === 'approval' ? '审批' : '推送'}
                  </Tag>
                </div>
                {node.type === 'approval' && (
                  <div style={{ marginTop: '8px' }}>
                    <div>审批人: {node.approvers?.length || 0}人</div>
                    <div>代审批人: {node.delegates?.length || 0}人</div>
                  </div>
                )}
                {node.type === 'push' && (
                  <div style={{ marginTop: '8px' }}>
                    <div>推送目标: {node.pushTargets?.length || 0}人</div>
                  </div>
                )}
              </Card>
            ))}
            {nodes.length === 0 && (
              <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                点击左侧按钮添加节点
              </div>
            )}
          </Card>
        </div>
      </div>

      <Modal
        title="编辑节点"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingNode(null);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveNode}
        >
          <Form.Item
            name="name"
            label="节点名称"
            rules={[{ required: true, message: '请输入节点名称' }]}
          >
            <Input />
          </Form.Item>

          {editingNode?.type === 'approval' && (
            <>
              <Form.Item
                name="approvers"
                label="审批人"
                rules={[{ required: true, message: '请选择审批人' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="选择审批人"
                  showSearch
                  filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                  }
                >
                  {users.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.username} ({user.role})
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="delegates"
                label="代审批人"
              >
                <Select
                  mode="multiple"
                  placeholder="选择代审批人"
                  showSearch
                  filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                  }
                >
                  {users.map(user => (
                    <Option key={user.id} value={user.id}>
                      {user.username} ({user.role})
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </>
          )}

          {editingNode?.type === 'push' && (
            <Form.Item
              name="pushTargets"
              label="推送目标"
              rules={[{ required: true, message: '请选择推送目标' }]}
            >
              <Select
                mode="multiple"
                placeholder="选择推送目标"
                showSearch
                filterOption={(input, option) =>
                  option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
              >
                {users.map(user => (
                  <Option key={user.id} value={user.id}>
                    {user.username} ({user.role})
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingNode(null);
                form.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Drawer>
  );
};

export default WorkflowDesigner;
