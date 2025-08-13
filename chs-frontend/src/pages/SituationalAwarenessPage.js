import React from 'react';
import { Row, Col } from 'antd';
import GisMap from '../components/GisMap';
import KpiDashboard from '../components/KpiDashboard';
import AlertsList from '../components/AlertsList';

const SituationalAwarenessPage = () => {
  return (
    <div>
      <Row gutter={16}>
        <Col span={16}>
          <GisMap />
        </Col>
        <Col span={8}>
          <KpiDashboard />
          <AlertsList />
        </Col>
      </Row>
    </div>
  );
};

export default SituationalAwarenessPage;
