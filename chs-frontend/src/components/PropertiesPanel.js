import React, { useEffect } from 'react';
import { Card, Form, Input, Typography } from 'antd';
import useWorkflowStore from '../store/useWorkflowStore';

const { Title } = Typography;

const PropertiesPanel = () => {
  const [form] = Form.useForm();
  const selectedNodeId = useWorkflowStore((state) => state.selectedNodeId);
  const { components, updateComponentParams } = useWorkflowStore();

  const selectedComponent = components.find(c => c.id === selectedNodeId);

  useEffect(() => {
    if (selectedComponent) {
      form.setFieldsValue({
        name: selectedComponent.name,
        ...selectedComponent.parameters,
      });
    }
  }, [selectedComponent, form]);

  if (!selectedComponent) {
    return (
      <Card>
        <Title level={4}>Properties</Title>
        <p>Select a component to see its properties.</p>
      </Card>
    );
  }

  const handleValuesChange = (changedValues, allValues) => {
    // This function is called on every form field change
    // We can debounce this if performance becomes an issue
    const { name, ...parameters } = allValues;
    updateComponentParams(selectedNodeId, { name, parameters });
  };

  return (
    <Card>
      <Title level={4}>Properties</Title>
      <p>ID: {selectedComponent.id}</p>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        key={selectedNodeId} // Re-mount the form when the node changes
      >
        <Form.Item label="Name" name="name">
          <Input />
        </Form.Item>
        {/* We can dynamically render form items based on component type later */}
        <Form.Item label="Parameter 1 (Example)" name="param1">
          <Input />
        </Form.Item>
        <Form.Item label="Parameter 2 (Example)" name="param2">
          <Input />
        </Form.Item>
      </Form>
    </Card>
  );
};

export default PropertiesPanel;
