import React, { useState, useCallback, useEffect } from 'react';

export const useResizable = (initialWidth: number, minWidth: number, maxWidth: number, direction: 'left' | 'right') => {
  const [width, setWidth] = useState(initialWidth);
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = useCallback(() => {
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (mouseMoveEvent: MouseEvent) => {
      if (isResizing) {
        let newWidth;
        if (direction === 'left') {
          newWidth = mouseMoveEvent.clientX;
        } else {
          newWidth = window.innerWidth - mouseMoveEvent.clientX;
        }
        
        if (newWidth >= minWidth && newWidth <= maxWidth) {
          setWidth(newWidth);
        }
      }
    },
    [isResizing, minWidth, maxWidth, direction]
  );

  useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [resize, stopResizing]);

  return { width, startResizing, isResizing };
};
