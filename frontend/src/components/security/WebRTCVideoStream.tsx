"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';

interface WebRTCVideoStreamProps {
  cameraId: string;
  location?: string;
}

export default function WebRTCVideoStream({ cameraId, location }: WebRTCVideoStreamProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const webSocketRef = useRef<WebSocket | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  const cleanup = useCallback(() => {
    console.log('Cleaning up connections...');
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    if (webSocketRef.current) {
      webSocketRef.current.close();
      webSocketRef.current = null;
    }
    if (videoRef.current) {
      const stream = videoRef.current.srcObject as MediaStream;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      videoRef.current.srcObject = null;
    }
  }, []);

  const retryConnection = useCallback(() => {
    console.log('Retrying connection...');
    cleanup();
    if (retryCount < maxRetries) {
      console.log(`Scheduling retry ${retryCount + 1}/${maxRetries}...`);
      retryTimeoutRef.current = setTimeout(() => {
        setRetryCount(prev => prev + 1);
        setError(null);
        setIsLoading(true);
        setupWebRTC();
      }, 2000);
    } else {
      setError('Connection failed. Please try again.');
      setIsLoading(false);
    }
  }, [retryCount, cleanup]);

  const setupWebRTC = useCallback(async () => {
    try {
      console.log('Setting up WebRTC connection...');
      cleanup();

      // Create WebSocket connection
      const wsUrl = `ws://${window.location.hostname}:8000/api/live-cameras/stream/${cameraId}`;
      console.log('Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);
      webSocketRef.current = ws;

      // Create RTCPeerConnection with performance-optimized configuration
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: ['stun:stun.l.google.com:19302'] }
        ],
        iceCandidatePoolSize: 10,
        bundlePolicy: 'max-bundle',
        rtcpMuxPolicy: 'require',
        iceTransportPolicy: 'all'
      });
      peerConnectionRef.current = pc;

      // Add transceiver for receiving video
      console.log('Adding video transceiver...');
      pc.addTransceiver('video', { direction: 'recvonly' });

      // Set up video element when we receive streams
      pc.ontrack = (event) => {
        console.log('Received track:', event.track.kind);
        if (videoRef.current && event.streams[0]) {
          console.log('Setting video source');
          
          // Configure video element for better performance
          videoRef.current.playsInline = true;
          videoRef.current.muted = true;
          videoRef.current.autoplay = true;
          
          // Set the stream
          videoRef.current.srcObject = event.streams[0];
          
          videoRef.current.onloadedmetadata = () => {
            console.log('Video metadata loaded, playing...');
            videoRef.current?.play().catch(err => {
              console.error('Error playing video:', err);
              setError('Failed to play video stream');
              setIsLoading(false);
            });
          };
          
          videoRef.current.onplaying = () => {
            console.log('Video is playing');
            setError(null);
            setIsLoading(false);
          };
        }
      };

      // Handle ICE candidate events
      pc.onicecandidate = (event) => {
        if (event.candidate && ws.readyState === WebSocket.OPEN) {
          console.log('Sending ICE candidate:', event.candidate);
          ws.send(JSON.stringify({
            type: 'candidate',
            candidate: event.candidate.toJSON()
          }));
        }
      };

      // Handle ICE connection state changes
      pc.oniceconnectionstatechange = () => {
        console.log('ICE connection state:', pc.iceConnectionState);
        if (pc.iceConnectionState === 'failed') {
          console.log('ICE connection failed, retrying...');
          retryConnection();
        } else if (pc.iceConnectionState === 'connected') {
          console.log('ICE connection established');
        }
      };

      // Handle connection state changes
      pc.onconnectionstatechange = () => {
        console.log('Connection state:', pc.connectionState);
        if (pc.connectionState === 'failed') {
          console.log('Connection failed, retrying...');
          retryConnection();
        } else if (pc.connectionState === 'connected') {
          console.log('Connection established');
          setError(null);
        }
      };

      // Handle WebSocket messages
      ws.onmessage = async (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received message:', message.type);
          
          if (message.type === 'offer') {
            console.log('Setting remote description (offer):', message);
            await pc.setRemoteDescription(new RTCSessionDescription(message));
            console.log('Creating answer');
            const answer = await pc.createAnswer();
            console.log('Setting local description:', answer);
            await pc.setLocalDescription(answer);
            console.log('Sending answer');
            ws.send(JSON.stringify({
              type: answer.type,
              sdp: answer.sdp
            }));
          } else if (message.type === 'candidate' && message.candidate) {
            console.log('Adding ICE candidate:', message.candidate);
            try {
              await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
            } catch (err) {
              console.error('Error adding ICE candidate:', err);
            }
          }
        } catch (err) {
          console.error('Error handling WebSocket message:', err);
          retryConnection();
        }
      };

      ws.onopen = () => {
        console.log('WebSocket connection established');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        if (event.code === 1008) {
          setError('Camera not found or not running');
          setIsLoading(false);
        } else {
          retryConnection();
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        retryConnection();
      };

    } catch (err) {
      console.error('WebRTC setup error:', err);
      retryConnection();
    }
  }, [cameraId, retryConnection, cleanup]);

  useEffect(() => {
    console.log('Component mounted or cameraId changed:', cameraId);
    setRetryCount(0);
    setError(null);
    setIsLoading(true);
    setupWebRTC();

    return cleanup;
  }, [cameraId, cleanup, setupWebRTC]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-gray-100 rounded-lg">
        <div className="flex flex-col items-center space-y-2">
          <div className="flex items-center space-x-2 text-red-500">
            <AlertTriangle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          {retryCount >= maxRetries && (
            <button
              onClick={() => {
                setRetryCount(0);
                setError(null);
                setIsLoading(true);
                setupWebRTC();
              }}
              className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      )}
      <video
        ref={videoRef}
        className="w-full h-full object-contain rounded-lg bg-black"
        playsInline
        muted
        autoPlay
      />
      {location && (
        <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm">
          {location}
        </div>
      )}
    </div>
  );
} 