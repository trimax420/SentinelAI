export interface Suspect {
    id: number;
    name: string;
    description?: string;
    aliases?: string[];
    physical_description?: string;
    priority_level?: number;
    is_active: boolean;
    created_at: string;
    updated_at?: string;
    images?: SuspectImage[];
    locations?: SuspectLocation[];
}

export interface SuspectImage {
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

export interface SuspectLocation {
    id: number;
    suspect_id: number;
    camera_id: string;
    timestamp: string;
    confidence?: number;
    coordinates?: {
        x: number;
        y: number;
    };
    movement_vector?: {
        direction: number;
        speed: number;
    };
    frame_number?: number;
}

export interface Case {
    id: number;
    case_number: string;
    title: string;
    description?: string;
    status: string;
    priority: number;
    created_at: string;
    updated_at?: string;
    suspects?: Suspect[];
} 