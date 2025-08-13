import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';

const KpiDashboard = () => {
  return (
    <Card title="Key Performance Indicators (KPIs)">
      <Row gutter={16}>
        <Col span={12}>
          <Statistic title="Total Supply" value={112893} suffix="m³" />
        </Col>
        <Col span={12}>
          <Statistic title="Energy Consumption" value={0.45} suffix="kWh/m³" />
        </Col>
      </Row>
      <Row gutter={16} style={{ marginTop: '16px' }}>
        <Col span={12}>
          <Statistic title="Water Quality" value={99.9} suffix="%" />
        </Col>
        <Col span={12}>
          <Statistic title="Pressure" value={3.5} suffix="bar" />
        </Col>
      </Row>
    </Card>
  );
};

export default KpiDashboard;
