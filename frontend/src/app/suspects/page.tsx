'use client';

import React, { useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge, BadgeProps } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { PlusCircle, Search, Upload, Eye } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";

interface SuspectImage {
  id: number;
  suspect_id: number;
  image_path: string;
  thumbnail_path?: string;
  confidence_score?: number;
  capture_date?: string;
  source?: string;
  is_primary: boolean;
  created_at: string;
}

interface Suspect {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  priority_level: number;
  images?: SuspectImage[];
  physical_description?: string;
}

interface SuspectLocation {
  id: number;
  suspect_id: number;
  camera_id: string;
  timestamp: string;
  confidence?: number;
  coordinates?: {
    x: number;
    y: number;
  };
  snapshot_path?: string;
}

interface NewSuspect {
  name: string;
  description?: string;
  physical_description?: string;
  priority_level: number;
}

export default function SuspectsPage() {
  const { toast } = useToast();
  const [suspects, setSuspects] = React.useState<Suspect[]>([]);
  const [selectedSuspect, setSelectedSuspect] = React.useState<Suspect | null>(null);
  const [locations, setLocations] = React.useState<SuspectLocation[]>([]);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [isAddingNew, setIsAddingNew] = React.useState(false);
  const [selectedImage, setSelectedImage] = React.useState<File | null>(null);
  const [newSuspect, setNewSuspect] = React.useState<NewSuspect>({
    name: '',
    description: '',
    physical_description: '',
    priority_level: 1
  });
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [isImageViewOpen, setIsImageViewOpen] = React.useState(false);
  const [selectedImageUrl, setSelectedImageUrl] = React.useState<string | null>(null);

  // Fetch suspects on component mount
  React.useEffect(() => {
    fetchSuspects();
  }, []);

  // Fetch suspect locations when a suspect is selected
  React.useEffect(() => {
    if (selectedSuspect) {
      fetchLocations(selectedSuspect.id);
    }
  }, [selectedSuspect]);

  const fetchSuspects = async () => {
    try {
      const response = await fetch('/api/suspects');
      if (!response.ok) {
        throw new Error('Failed to fetch suspects');
      }
      const data = await response.json();
      setSuspects(data as Suspect[]);
    } catch (error) {
      console.error('Error fetching suspects:', error);
      setError('Failed to fetch suspects');
    } finally {
      setLoading(false);
    }
  };

  const fetchLocations = async (suspectId: number) => {
    try {
      const response = await fetch(`/api/suspects/${suspectId}/locations`);
      if (!response.ok) {
        throw new Error('Failed to fetch locations');
      }
      const data = await response.json();
      setLocations(data as SuspectLocation[]);
    } catch (error) {
      console.error('Error fetching locations:', error);
      setLocations([]);
    }
  };

  const handleImageUpload = async (suspectId: number) => {
    if (!selectedImage) return;

    try {
      await api.uploadSuspectImage(suspectId, selectedImage);
      setSelectedImage(null);
      // Refresh suspect data
      fetchSuspects();
      toast({
        title: "Success",
        description: "Image uploaded successfully",
      });
    } catch (error) {
      console.error('Error uploading image:', error);
      toast({
        title: "Error",
        description: error instanceof Error 
          ? error.message 
          : "Failed to upload image. Please ensure the image contains a clearly visible face.",
        variant: "destructive",
      });
    }
  };

  const handleCreateSuspect = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/suspects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newSuspect.name,
          description: newSuspect.description || '',
          physical_description: newSuspect.physical_description || '',
          priority_level: newSuspect.priority_level,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create suspect');
      }

      const createdSuspect = await response.json();
      setSuspects(prev => [...prev, createdSuspect as Suspect]);
      setNewSuspect({
        name: '',
        description: '',
        physical_description: '',
        priority_level: 1
      });
      setIsDialogOpen(false);
      toast({
        title: "Success",
        description: "Suspect created successfully",
      });
    } catch (error) {
      console.error('Error creating suspect:', error);
      toast({
        title: "Error",
        description: "Failed to create suspect",
        variant: "destructive",
      });
    }
  };

  // Filter suspects based on search query
  const filteredSuspects = React.useMemo(() => {
    return suspects.filter(suspect =>
      suspect?.name?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [suspects, searchQuery]);

  // Add remove handler
  const handleRemoveSuspect = async (suspectId: number) => {
    if (!confirm("Are you sure you want to remove this suspect? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`/api/suspects/${suspectId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove suspect');
      }

      // Remove from state
      setSuspects(prev => prev.filter(s => s.id !== suspectId));
      setSelectedSuspect(null);
      toast({
        title: "Success",
        description: "Suspect removed successfully",
      });
    } catch (error) {
      console.error('Error removing suspect:', error);
      toast({
        title: "Error",
        description: "Failed to remove suspect",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Suspects Management</h1>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" />
              Add New Suspect
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add New Suspect</DialogTitle>
              <DialogDescription>
                Enter the details of the new suspect. All fields except aliases are required.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={newSuspect.name}
                  onChange={(e) => setNewSuspect({ ...newSuspect, name: e.target.value })}
                  placeholder="Enter suspect's name"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newSuspect.description || ''}
                  onChange={(e) => setNewSuspect({ ...newSuspect, description: e.target.value })}
                  placeholder="Enter description"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="physical_description">Physical Description</Label>
                <Textarea
                  id="physical_description"
                  value={newSuspect.physical_description || ''}
                  onChange={(e) => setNewSuspect({ ...newSuspect, physical_description: e.target.value })}
                  placeholder="Enter physical description"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="priority_level">Priority Level</Label>
                <Select
                  value={newSuspect.priority_level?.toString() || '1'}
                  onValueChange={(value) => setNewSuspect({ ...newSuspect, priority_level: Number(value) })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select priority level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1</SelectItem>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                    <SelectItem value="5">5</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="image">Suspect Image</Label>
                <Input
                  id="image"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSelectedImage(e.target.files?.[0] || null)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button className="mr-2" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateSuspect}>Create Suspect</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Search and List Panel */}
        <div className="md:col-span-1">
          <Card>
            <CardHeader>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search suspects..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredSuspects.map((suspect) => (
                  <div
                    key={suspect.id}
                    className={cn(
                      "p-2 rounded cursor-pointer hover:bg-accent",
                      selectedSuspect?.id === suspect.id && "bg-accent"
                    )}
                    onClick={() => setSelectedSuspect(suspect)}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{suspect.name}</span>
                      <div className={cn(
                        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                        suspect.is_active ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                      )}>
                        {suspect.is_active ? 'Active' : 'Inactive'}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Priority: {suspect.priority_level || 'Not set'}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Details Panel */}
        <div className="md:col-span-2">
          <Card>
            <div className="p-6">
              <CardContent>
                {selectedSuspect ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-2xl font-bold">{selectedSuspect.name}</h2>
                      <div className="flex gap-2">
                        <Button
                          variant="destructive"
                          onClick={() => handleRemoveSuspect(selectedSuspect.id)}
                        >
                          Remove Suspect
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium">Description</label>
                        <Textarea
                          value={selectedSuspect.description || ''}
                          readOnly
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium">Physical Description</label>
                        <Textarea
                          value={selectedSuspect.physical_description || ''}
                          readOnly
                          className="mt-1"
                        />
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium mb-2">Recent Locations</h3>
                      <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                        {locations.map((location) => (
                          <div
                            key={location.id}
                            className="p-2 border rounded flex justify-between items-center"
                          >
                            <div>
                              <div className="flex items-center text-sm">
                                <span className="font-medium mr-2">Camera:</span> 
                                <span>{location.camera_id}</span>
                              </div>
                              {location.confidence && (
                                <p className="text-sm text-gray-600">
                                  Confidence: {(location.confidence * 100).toFixed(1)}%
                                </p>
                              )}
                              <span className="text-xs text-gray-500">
                                {new Date(location.timestamp).toLocaleString()}
                              </span>
                            </div>
                            {location.snapshot_path && (
                              <button
                                onClick={() => {
                                  if (location.snapshot_path) {
                                    setSelectedImageUrl(location.snapshot_path); 
                                    setIsImageViewOpen(true);
                                  }
                                }}
                                title="View Snapshot for this Location"
                                className="text-blue-600 hover:text-blue-800 ml-2 p-1 rounded hover:bg-blue-100"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium mb-2">Images</h3>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {selectedSuspect.images?.map((image) => (
                          <div key={image.id} className="relative group aspect-square">
                            {(() => {
                              // Construct the API URL for the suspect image
                              const imageUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/suspects/image/${image.id}`;
                              return (
                                <>
                                  <img
                                    src={imageUrl} // Use the constructed API URL
                                    alt={`Suspect ${selectedSuspect.name}`}
                                    className="object-cover rounded w-full h-full"
                                    onError={(e) => { e.currentTarget.src = '/placeholder-image.png'; }} // Fallback image
                                  />
                                  {image.is_primary && (
                                    <div className="absolute top-1 right-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 z-10">
                                      Primary
                                    </div>
                                  )}
                                  {/* Overlay with View Button */}
                                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 flex items-center justify-center transition-opacity duration-200 opacity-0 group-hover:opacity-100">
                                    <button
                                      onClick={() => {
                                        setSelectedImageUrl(imageUrl); // Use the constructed API URL here too
                                        setIsImageViewOpen(true);
                                      }}
                                      title="View Image"
                                      className="text-white p-2 bg-black bg-opacity-50 rounded-full hover:bg-opacity-75"
                                    >
                                      <Eye className="h-5 w-5" />
                                    </button>
                                  </div>
                                </>
                              );
                            })()}
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 space-y-2">
                        <h4 className="text-sm font-medium">Upload New Image</h4>
                        <div className="flex items-center gap-2">
                          <Input
                            type="file"
                            accept="image/*"
                            onChange={(e) => setSelectedImage(e.target.files?.[0] || null)}
                            className="flex-1"
                          />
                          <Button
                            onClick={() => selectedSuspect && handleImageUpload(selectedSuspect.id)}
                            disabled={!selectedImage}
                          >
                            <Upload className="mr-2 h-4 w-4" />
                            Upload
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-muted-foreground">
                      Select a suspect from the list or create a new one
                    </p>
                  </div>
                )}
              </CardContent>
            </div>
          </Card>
        </div>
      </div>

      {/* Image Viewer Modal */}
      <Dialog open={isImageViewOpen} onOpenChange={setIsImageViewOpen}>
        <DialogContent className="max-w-4xl">
          {selectedImageUrl && (
            <img 
              src={selectedImageUrl} 
              alt="Suspect Image"
              className="max-w-full h-auto mx-auto rounded"
            />
          )}
        </DialogContent>
      </Dialog>

    </div>
  );
} 