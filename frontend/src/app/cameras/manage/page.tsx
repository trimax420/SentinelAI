"use client";

import React, { useState, useEffect } from 'react';
import { Camera as CameraIcon, Play, Square, Plus, PlayCircle, StopCircle, AlertCircle, Settings, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { Button } from "@/components/ui/button";
// Removed unused imports and fixed module path if necessary
import { toast } from "@/components/ui/use-toast";
import { api } from "@/lib/api";

interface CameraFormData {
  camera_id: string;
  source: string;
  zone_name: string;
}

interface CameraStatusResponse {
  [key: string]: {
    source: string;
    zone_name?: string;
    status: string;
  };
}

interface AlertState {
  type: 'success' | 'error';
  message: string;
}

interface Camera {
  camera_id: string;
  source: string;
  zone_name?: string;
  status?: 'running' | 'stopped';
}

export default function ManageCamerasPage() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState<CameraFormData>({
    camera_id: '',
    source: '',
    zone_name: '',
  });
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCameras();
    const interval = setInterval(fetchCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchCameras = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/live-cameras/status/');
      if (response.ok) {
        const data: CameraStatusResponse = await response.json();
        const camerasWithStatus: Camera[] = Object.entries(data).map(([id, info]) => ({
          camera_id: id,
          source: info.source,
          zone_name: info.zone_name || '',
          status: info.status === 'running' ? 'running' : 'stopped'
        }));
        setCameras(camerasWithStatus);
        setError(null);
      }
    } catch (err) {
      console.error("Failed to fetch cameras:", err);
      setError("Failed to load cameras.");
    }
    setLoading(false);
  };

  const validateCameraId = (id: string): boolean => {
    return /^[a-zA-Z0-9-]+$/.test(id);
  };

  const showAlert = (type: 'success' | 'error', message: string) => {
    setAlert({ type, message });
    setTimeout(() => setAlert(null), 5000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateCameraId(formData.camera_id)) {
      showAlert('error', 'Camera ID can only contain letters, numbers, and hyphens');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/live-cameras/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await fetchCameras();
        setFormData({ camera_id: '', source: '', zone_name: '' });
        setShowAddForm(false);
        showAlert('success', 'Camera registered successfully');
      } else {
        const error = await response.json();
        showAlert('error', error.message || 'Failed to register camera');
      }
    } catch (error) {
      console.error('Failed to register camera:', error);
      showAlert('error', 'Failed to register camera. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStartCamera = async (id: string) => {
    try {
      const response = await fetch('/api/live-cameras/start/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ camera_id: id }),
      });

      if (response.ok) {
        setCameras(cameras.map(cam => 
          cam.camera_id === id ? { ...cam, status: 'running' } : cam
        ));
        showAlert('success', 'Camera started successfully');
      } else {
        const error = await response.json();
        showAlert('error', error.message || 'Failed to start camera');
      }
    } catch (error) {
      console.error('Failed to start camera:', error);
      showAlert('error', 'Failed to start camera');
    }
  };

  const handleStopCamera = async (id: string) => {
    try {
      const response = await fetch('/api/live-cameras/stop/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ camera_id: id }),
      });

      if (response.ok) {
        setCameras(cameras.map(cam => 
          cam.camera_id === id ? { ...cam, status: 'stopped' } : cam
        ));
        showAlert('success', 'Camera stopped successfully');
      } else {
        const error = await response.json();
        showAlert('error', error.message || 'Failed to stop camera');
      }
    } catch (error) {
      console.error('Failed to stop camera:', error);
      showAlert('error', 'Failed to stop camera');
    }
  };

  const handleStartAll = async () => {
    try {
      const response = await fetch('/api/live-cameras/start-all/', {
        method: 'POST',
      });

      if (response.ok) {
        setCameras(cameras.map(cam => ({ ...cam, status: 'running' })));
        showAlert('success', 'All cameras started successfully');
      } else {
        const error = await response.json();
        showAlert('error', error.message || 'Failed to start all cameras');
      }
    } catch (error) {
      console.error('Failed to start all cameras:', error);
      showAlert('error', 'Failed to start all cameras');
    }
  };

  const handleStopAll = async () => {
    try {
      const response = await fetch('/api/live-cameras/stop-all/', {
        method: 'POST',
      });

      if (response.ok) {
        setCameras(cameras.map(cam => ({ ...cam, status: 'stopped' })));
        showAlert('success', 'All cameras stopped successfully');
      } else {
        const error = await response.json();
        showAlert('error', error.message || 'Failed to stop all cameras');
      }
    } catch (error) {
      console.error('Failed to stop all cameras:', error);
      showAlert('error', 'Failed to stop all cameras');
    }
  };

  const handleDeleteCamera = async (cameraId: string) => {
    if (!confirm(`Are you sure you want to delete camera ${cameraId}? This action cannot be undone.`)) {
      return;
    }
    try {
      const response = await fetch(`/api/live-cameras/delete/${cameraId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete camera ${cameraId}`);
      }
      setCameras(prevCameras => prevCameras.filter((cam) => cam.camera_id !== cameraId));
      toast({ title: "Success", description: `Camera ${cameraId} deleted successfully.` });
    } catch (error) {
      console.error("Error deleting camera:", error);
      toast({
        title: "Error",
        description: `Failed to delete camera ${cameraId}.`, 
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {alert && (
          <div className={`p-4 rounded-md ${
            alert.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 mr-2" />
              <p>{alert.message}</p>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Camera Management</h1>
              <p className="text-sm text-gray-500">Add, configure, and monitor your security cameras</p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={handleStartAll}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700"
              >
                <PlayCircle className="h-4 w-4 mr-2" />
                Start All
              </button>
              <button
                onClick={handleStopAll}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
              >
                <StopCircle className="h-4 w-4 mr-2" />
                Stop All
              </button>
              <button
                onClick={() => setShowAddForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Camera
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading && <div className="col-span-3">Loading...</div>}
            {error && <div className="col-span-3">{error}</div>}
            {!loading && !error && cameras.map((camera) => (
              <div key={camera.camera_id} className="bg-white border rounded-lg shadow-sm">
                <div className="p-4 border-b">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      <CameraIcon className="h-5 w-5 text-gray-400 mr-2" />
                      <h3 className="text-lg font-medium text-gray-900">{camera.camera_id}</h3>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        camera.status === 'running'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {camera.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mb-1">Zone: {camera.zone_name || 'Not specified'}</p>
                  <p className="text-xs text-gray-400 truncate">Source: {camera.source}</p>
                </div>
                <div className="p-4 bg-gray-50 flex justify-between items-center">
                  <div className="flex space-x-2">
                    {camera.status === 'stopped' ? (
                      <button
                        onClick={() => handleStartCamera(camera.camera_id)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded text-white bg-green-600 hover:bg-green-700"
                      >
                        <Play className="h-4 w-4 mr-1" />
                        Start
                      </button>
                    ) : (
                      <button
                        onClick={() => handleStopCamera(camera.camera_id)}
                        className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded text-white bg-red-600 hover:bg-red-700"
                      >
                        <Square className="h-4 w-4 mr-1" />
                        Stop
                      </button>
                    )}
                    <Link
                      href={`/cameras/${camera.camera_id}/settings`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <Settings className="h-4 w-4 mr-1" />
                      Configure
                    </Link>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={() => handleDeleteCamera(camera.camera_id)}
                      title={`Delete camera ${camera.camera_id}`}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {cameras.length === 0 && (
            <div className="text-center py-12">
              <CameraIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No cameras</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by adding a new camera.</p>
              <div className="mt-6">
                <button
                  onClick={() => setShowAddForm(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Camera
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">Add New Camera</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Camera ID</label>
                <input
                  type="text"
                  value={formData.camera_id}
                  onChange={(e) => setFormData({ ...formData, camera_id: e.target.value.trim() })}
                  className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                    formData.camera_id && !validateCameraId(formData.camera_id)
                      ? 'border-red-300'
                      : 'border-gray-300'
                  }`}
                  required
                  placeholder="Enter a unique camera ID (e.g., front-door)"
                />
                {formData.camera_id && !validateCameraId(formData.camera_id) && (
                  <p className="mt-1 text-xs text-red-600">
                    Invalid format. Use only letters, numbers, and hyphens.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Source</label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                  placeholder="rtsp://camera-ip:port/stream or /dev/video0"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Enter RTSP URL or device path
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Zone Name (Optional)</label>
                <input
                  type="text"
                  value={formData.zone_name}
                  onChange={(e) => setFormData({ ...formData, zone_name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  placeholder="e.g., Main Entrance, Jewelry Section"
                />
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || Boolean(formData.camera_id && !validateCameraId(formData.camera_id))}
                  className={`px-4 py-2 text-sm font-medium text-white rounded-md ${
                    isSubmitting || (formData.camera_id && !validateCameraId(formData.camera_id))
                      ? 'bg-blue-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {isSubmitting ? 'Adding...' : 'Add Camera'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}