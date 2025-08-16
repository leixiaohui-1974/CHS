import React from 'react';

/**
 * A simple modal component.
 * @param {object} props - The component's props.
 * @param {boolean} props.show - Whether the modal should be displayed.
 * @param {function} props.onClose - Callback function to close the modal.
 * @param {React.ReactNode} props.children - The content to display inside the modal.
 * @param {string} [props.title] - An optional title for the modal header.
 */
const Modal = ({ show, onClose, children, title }) => {
  if (!show) {
    return null;
  }

  const modalStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  };

  const modalContentStyle = {
    backgroundColor: '#fff',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
    width: '80%',
    maxWidth: '700px',
    zIndex: 1001,
  };

  const modalHeaderStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #eee',
    paddingBottom: '10px',
    marginBottom: '20px',
  };

  const modalTitleStyle = {
    margin: 0,
    fontSize: '1.5em',
  };

  const closeButtonStyle = {
    background: 'none',
    border: 'none',
    fontSize: '1.5em',
    cursor: 'pointer',
  };

  return (
    <div style={modalStyle} onClick={onClose}>
      <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
        <div style={modalHeaderStyle}>
          <h2 style={modalTitleStyle}>{title || '详情'}</h2>
          <button style={closeButtonStyle} onClick={onClose}>
            &times;
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

export default Modal;
