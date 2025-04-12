"use client";

import { useState } from 'react';
import { Search, User, Shield, Clock, MapPin } from 'lucide-react';

interface StaffMember {
  id: string;
  name: string;
  role: 'security' | 'sales' | 'manager';
  status: 'active' | 'break' | 'offline';
  location: string;
  lastActive: Date;
}

const staffMembers: StaffMember[] = [
  {
    id: '1',
    name: 'John Smith',
    role: 'security',
    status: 'active',
    location: 'Perfume Section',
    lastActive: new Date(),
  },
  {
    id: '2',
    name: 'Sarah Johnson',
    role: 'sales',
    status: 'break',
    location: 'Staff Room',
    lastActive: new Date(Date.now() - 15 * 60000), // 15 minutes ago
  },
  {
    id: '3',
    name: 'Mike Wilson',
    role: 'manager',
    status: 'active',
    location: 'Office',
    lastActive: new Date(),
  },
  {
    id: '4',
    name: 'Emily Brown',
    role: 'security',
    status: 'offline',
    location: 'Off Duty',
    lastActive: new Date(Date.now() - 2 * 3600000), // 2 hours ago
  },
];

export default function PersonnelPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const filteredStaff = staffMembers.filter((staff) => {
    const matchesSearch = staff.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || staff.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || staff.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  const getStatusColor = (status: StaffMember['status']) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'break':
        return 'bg-yellow-100 text-yellow-800';
      case 'offline':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleIcon = (role: StaffMember['role']) => {
    switch (role) {
      case 'security':
        return <Shield className="h-5 w-5" />;
      case 'manager':
        return <User className="h-5 w-5" />;
      default:
        return <User className="h-5 w-5" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Personnel Management</h1>
        <button className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600">
          Add Staff Member
        </button>
      </div>

      <div className="flex space-x-4">
        <div className="flex-1">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="Search staff members..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <select
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          <option value="all">All Roles</option>
          <option value="security">Security</option>
          <option value="sales">Sales</option>
          <option value="manager">Manager</option>
        </select>
        <select
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="break">On Break</option>
          <option value="offline">Offline</option>
        </select>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredStaff.map((staff) => (
            <li key={staff.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {getRoleIcon(staff.role)}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {staff.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {staff.role.charAt(0).toUpperCase() + staff.role.slice(1)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-500">
                      <div className="flex items-center">
                        <MapPin className="h-4 w-4 mr-1" />
                        {staff.location}
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {staff.lastActive.toLocaleTimeString()}
                      </div>
                    </div>
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                        staff.status
                      )}`}
                    >
                      {staff.status.charAt(0).toUpperCase() + staff.status.slice(1)}
                    </span>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
} 