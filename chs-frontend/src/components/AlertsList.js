import React from 'react';
import { Card, List } from 'antd';

const alertsData = [
  {
    id: 1,
    message: 'XX pump station outlet pressure is over limit',
    timestamp: '2023-10-27 10:30:00',
  },
  {
    id: 2,
    message: 'Low water level detected in Reservoir B',
    timestamp: '2023-10-27 10:35:00',
  },
  {
    id: 3,
    message: 'Communication failure with Valve C',
    timestamp: '2023-10-27 10:40:00',
  },
];

const AlertsList = () => {
  return (
    <Card title="Alerts & Events" style={{ marginTop: '16px' }}>
      <List
        dataSource={alertsData}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={item.message}
              description={item.timestamp}
            />
          </List.Item>
        )}
      />
    </Card>
  );
};

export default AlertsList;
