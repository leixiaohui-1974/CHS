import React from 'react';

const MainLayout = ({ children }) => {
  return (
    <div>
      {/* Shared header, sidebar, etc. can go here */}
      <main>{children}</main>
    </div>
  );
};

export default MainLayout;
