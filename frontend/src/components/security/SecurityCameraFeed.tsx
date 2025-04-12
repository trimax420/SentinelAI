"use client";

import React, { useEffect, useState, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';

interface SecurityCameraFeedProps {
  cameraId: string;
  location: string;
}

interface Detection {
  id: number;
  timestamp: string;
  camera_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
  class_id: number;
  class_name: string;
}

const SecurityCameraFeed: React.FC<SecurityCameraFeedProps> = ({ cameraId, location }) => {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [detectionsError, setDetectionsError] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const frameIntervalRef = useRef<number>();

  // Handle video stream
  useEffect(() => {
    const loadFrame = () => {
      if (imgRef.current) {
        // Use the correct API path format with a timestamp to prevent caching
        imgRef.current.src = `/api/live-cameras/frame/${cameraId}/?t=${Date.now()}`;
      }
    };

    const startFrameLoop = () => {
      // Load initial frame
      loadFrame();

      // Set up interval to refresh frame using window.setInterval
      frameIntervalRef.current = window.setInterval(loadFrame, 1000); // Update every second
    };

    if (imgRef.current) {
      const img = imgRef.current;
      
      // Set up error handling for the stream
      img.onerror = () => {
        setStreamError('Failed to load camera feed');
        setIsLoading(false);
        // Clear existing interval
        if (frameIntervalRef.current) {
          window.clearInterval(frameIntervalRef.current);
        }
        // Set fallback image
        if (imgRef.current) {
          imgRef.current.src = '/placeholder-camera.jpg';
        }
        // Retry after 3 seconds
        setTimeout(startFrameLoop, 3000);
      };

      img.onload = () => {
        setStreamError(null);
        setIsLoading(false);
      };

      // Start the frame loop
      startFrameLoop();
    }

    return () => {
      // Clean up interval on unmount
      if (frameIntervalRef.current) {
        window.clearInterval(frameIntervalRef.current);
      }
    };
  }, [cameraId]);

  // Handle detections
  useEffect(() => {
    const fetchDetections = async () => {
      try {
        // Use the correct API path for detections
        const response = await fetch(`/api/detection/detections/?camera_id=${cameraId}`);
        if (!response.ok) {
          throw new Error('Failed to fetch detections');
        }
        const data = await response.json();
        setDetections(data);
        setDetectionsError(null);
      } catch (err) {
        setDetectionsError('Failed to load detections');
        console.error('Error fetching detections:', err);
      }
    };

    fetchDetections();

    // Set up interval to refresh detections
    const detectionInterval = window.setInterval(fetchDetections, 3000);

    return () => {
      window.clearInterval(detectionInterval);
    };
  }, [cameraId]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="relative h-64 bg-gray-100 rounded-lg overflow-hidden">
      {/* Camera feed */}
      <img
        ref={imgRef}
        alt={`Camera feed from ${location}`}
        className="absolute inset-0 w-full h-full object-cover"
      />
      
      {streamError && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 bg-opacity-90">
          <div className="text-red-600 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            {streamError}
          </div>
        </div>
      )}
      
      {/* Detection overlays */}
      {!streamError && !detectionsError && detections.map((detection) => (
        <div
          key={detection.id}
          className="absolute w-8 h-8 border-2 border-red-500 rounded-full transform -translate-x-1/2 -translate-y-1/2"
          style={{
            left: `${detection.x * 100}%`,
            top: `${detection.y * 100}%`,
          }}
        >
          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2">
            <div className="bg-red-500 text-white text-xs px-2 py-1 rounded">
              {Math.round(detection.confidence * 100)}%
            </div>
          </div>
        </div>
      ))}

      {/* Alert Indicator */}
      {!streamError && !detectionsError && detections.some(d => d.confidence > 0.9) && (
        <div className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full">
          <AlertTriangle className="h-5 w-5" />
        </div>
      )}
    </div>
  );
};

export default SecurityCameraFeed; 