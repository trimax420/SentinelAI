"use client";

import { useState, useEffect } from 'react';
import { AlertTriangle, Search, Filter, Clock, MapPin, Camera, Eye, CheckCircle, X, LayoutGrid, List } from 'lucide-react';
import { api } from '@/lib/api';
import type { Alert } from '@/lib/api';

// Add Modal component (or use a pre-built one if available in the project)
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger, // We might not need trigger if controlled manually
  DialogClose
} from "@/components/ui/dialog";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<number | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(12); // Adjust as needed

  const getSnapshotUrl = (alertId: number): string => {
    return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/alerts/snapshot/${alertId}`;
  };

  useEffect(() => {
    let mounted = true;
    let wsUnsubscribe: (() => void) | null = null;

    // Fetch initial alerts
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const data = await api.getAlerts({
          acknowledged: false
        });
        if (mounted) {
          // Transform the data to include direct snapshot URLs
          const alertsWithUrls = data.map(alert => ({
            ...alert,
            snapshot_path: getSnapshotUrl(alert.id)
          }));
          setAlerts(alertsWithUrls);
          setError(null);
          setRetryCount(0);
        }
      } catch (error) {
        console.error('Error fetching alerts:', error);
        if (mounted) {
          setError('Failed to load alerts. Retrying...');
          if (retryCount < 3) {
            setTimeout(() => {
              setRetryCount(prev => prev + 1);
            }, 5000);
          } else {
            setError('Failed to load alerts. Please check your connection and try again.');
          }
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Setup WebSocket connection
    const setupWebSocket = () => {
      try {
        wsUnsubscribe = api.subscribeToAlerts((alert: Alert | Alert[]) => {
          if (mounted) {
            // Defensively handle if it's an array, though unlikely based on logic
            const alertsToAdd = Array.isArray(alert) ? alert : [alert];
            
            setAlerts((prevAlerts: Alert[]) => {
              let updatedAlerts = [...prevAlerts];
              alertsToAdd.forEach(newAlert => {
                const exists = updatedAlerts.some(a => a.id === newAlert.id);
                if (exists) {
                  updatedAlerts = updatedAlerts.map(a => 
                    a.id === newAlert.id ? { ...newAlert, snapshot_path: getSnapshotUrl(newAlert.id) } : a
                  );
                } else {
                  updatedAlerts.unshift({ ...newAlert, snapshot_path: getSnapshotUrl(newAlert.id) });
                }
              });
              return updatedAlerts;
            });
          }
        });
      } catch (error) {
        console.error('WebSocket connection error:', error);
        if (mounted) {
          setError('Real-time updates unavailable. Please refresh the page to try again.');
        }
      }
    };

    fetchAlerts();
    setupWebSocket();

    return () => {
      mounted = false;
      if (wsUnsubscribe) {
        wsUnsubscribe();
      }
    };
  }, [retryCount, typeFilter, severityFilter]);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await api.acknowledgeAlert(alertId);
      // Refresh alerts after acknowledgment
      const updatedAlerts = await api.getAlerts();
      setAlerts(updatedAlerts);
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleExport = async () => {
    try {
      const allAlerts = await api.getAlerts();
      const now = new Date().toISOString().split('T')[0];

      // Create CSV content
      const csvContent = [
        // CSV headers
        ['ID', 'Timestamp', 'Type', 'Severity', 'Track ID', 'Description', 'Acknowledged', 'Acknowledged By', 'Acknowledged At'].join(','),
        // CSV rows
        ...allAlerts.map(alert => [
          alert.id,
          alert.timestamp,
          alert.alert_type,
          alert.severity,
          alert.track_id,
          alert.description ? `"${alert.description.replace(/"/g, '""')}"` : '', // Handle optional description
          alert.acknowledged,
          alert.acknowledged_by || '',
          alert.acknowledged_at || ''
        ].join(','))
      ].join('\n');

      // Create and download the file
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `alerts-export-${now}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting alerts:', error);
      setError('Failed to export alerts. Please try again.');
    }
  };

  const filteredAlerts = alerts.filter((alert) => {
    const matchesSearch = (alert.description || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                         alert.alert_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter;
    const matchesType = typeFilter === 'all' || alert.alert_type === typeFilter;
    return matchesSearch && matchesSeverity && matchesType;
  });

  // Calculate pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentAlerts = filteredAlerts.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredAlerts.length / itemsPerPage);

  // Change page handler
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  const formatDate = (dateInput: string | Date | null | undefined): string => {
    if (!dateInput) return 'N/A'; 
    
    let date: Date;
    try {
      if (dateInput instanceof Date) {
        date = dateInput;
      } else {
        // If it's a string, try parsing it
        date = new Date(String(dateInput)); 
      }

      // Check for invalid date
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      return date.toLocaleString();
    } catch (error) {
      console.error('Error formatting date:', error);
      // Return the original input if formatting fails
      return String(dateInput); 
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-semibold text-gray-900">Recent Alerts</h1>
          <div className="text-sm text-gray-500">
            Showing {currentAlerts.length} alerts (Page {currentPage} of {totalPages}, {filteredAlerts.length} total filtered)
          </div>
        </div>
        <div className="flex space-x-4">
          <div className="flex rounded-md shadow-sm">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 rounded-l-md border ${
                viewMode === 'grid' 
                  ? 'bg-blue-50 border-blue-500 text-blue-600' 
                  : 'bg-white border-gray-300 text-gray-500'
              }`}
            >
              <LayoutGrid className="h-5 w-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 rounded-r-md border-t border-r border-b -ml-px ${
                viewMode === 'list' 
                  ? 'bg-blue-50 border-blue-500 text-blue-600' 
                  : 'bg-white border-gray-300 text-gray-500'
              }`}
            >
              <List className="h-5 w-5" />
            </button>
          </div>
          <button 
            onClick={handleExport}
            className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
          >
            Export Alerts
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search alerts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <select
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value === 'all' ? 'all' : Number(e.target.value))}
        >
          <option value="all">All Severity</option>
          <option value="3">High</option>
          <option value="2">Medium</option>
          <option value="1">Low</option>
        </select>
        <select
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="all">All Types</option>
          <option value="suspect_detected">Suspect Detected</option>
          <option value="suspicious_pose">Suspicious Pose</option>
          <option value="loitering">Loitering</option>
        </select>
      </div>

      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {currentAlerts.map((alert) => (
            <div key={alert.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div className="relative h-48">
                <img
                  src={alert.snapshot_path}
                  alt={alert.description}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-2 left-2">
                  <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                    New
                  </span>
                </div>
                <div className="absolute top-2 right-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                    alert.severity === 3 ? 'bg-red-100 text-red-800' :
                    alert.severity === 2 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.severity === 3 ? 'High' :
                     alert.severity === 2 ? 'Medium' : 'Low'}
                  </span>
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
                  <div className="flex items-center text-white space-x-2">
                    <Camera className="h-4 w-4" />
                    <span className="text-sm font-medium">{alert.alert_type}</span>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <div className="text-sm font-medium text-gray-900 mb-1">
                  {alert.description}
                </div>
                <div className="text-xs text-gray-500 mb-2">
                  {alert.track_id}
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    {formatDate(alert.timestamp)}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        setSelectedAlert(alert);
                        setIsImageModalOpen(true);
                      }}
                      title="View Snapshot"
                      className="text-blue-600 hover:text-blue-800"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    {!alert.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        title="Acknowledge Alert"
                        className="text-green-600 hover:text-green-800"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <ul className="divide-y divide-gray-200">
            {currentAlerts.map((alert) => (
              <li key={alert.id} className="hover:bg-gray-50">
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <AlertTriangle className={`h-5 w-5 ${
                        alert.severity === 3 ? 'text-red-500' :
                        alert.severity === 2 ? 'text-yellow-500' : 'text-blue-500'
                      }`} />
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {alert.description}
                        </div>
                        <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            {formatDate(alert.timestamp)}
                          </div>
                          <div className="flex items-center">
                            <MapPin className="h-4 w-4 mr-1" />
                            {alert.track_id}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        alert.severity === 3 ? 'bg-red-100 text-red-800' :
                        alert.severity === 2 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.severity === 3 ? 'High' :
                         alert.severity === 2 ? 'Medium' : 'Low'}
                      </span>
                      <button
                        onClick={() => {
                          setSelectedAlert(alert);
                          setIsImageModalOpen(true);
                        }}
                        title="View Snapshot"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <Eye className="h-5 w-5" />
                      </button>
                      {!alert.acknowledged && (
                        <button
                          onClick={() => handleAcknowledge(alert.id)}
                          title="Acknowledge Alert"
                          className="text-green-600 hover:text-green-800"
                        >
                          <CheckCircle className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
          <button
            onClick={() => paginate(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => paginate(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}

      {/* Image Modal using Dialog */}
      <Dialog open={isImageModalOpen} onOpenChange={setIsImageModalOpen}>
        <DialogContent className="max-w-3xl">
          {selectedAlert && (
            <>
              <DialogHeader>
                <DialogTitle>Alert Snapshot: {selectedAlert.description}</DialogTitle>
              </DialogHeader>
              <div className="mt-4">
                <img 
                  src={selectedAlert.snapshot_path} 
                  alt={`Snapshot for alert ${selectedAlert.id}`}
                  className="max-w-full h-auto mx-auto rounded"
                />
                <div className="mt-2 text-sm text-gray-600">
                  <p><span className="font-semibold">Timestamp:</span> {formatDate(selectedAlert.timestamp)}</p>
                  <p><span className="font-semibold">Type:</span> {selectedAlert.alert_type}</p>
                  <p><span className="font-semibold">Severity:</span> {selectedAlert.severity}</p>
                  {selectedAlert.track_id && <p><span className="font-semibold">Track ID:</span> {selectedAlert.track_id}</p>}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

    </div>
  );
} 