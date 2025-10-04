export type PanelKind = "youtube" | "paper" | "model";

export interface Item {
  id: number;  
  title: string;
  // Database IDs needed for like/dislike functionality
  database_id?: number; // The actual database ID (youtube_id or paper_id)
  target_type?: "youtube" | "paper"; // The type for database operations
  project_id?: number; // The project this item belongs to
  liked_disliked_id?: number; // The like record ID for updates
  meta: {
    channel?: string;
    duration?: string;
    views?: number;  
    likes?: number;  
    video_url?: string;
    venue?: string;
    year?: number;
    framework?: string;
    vram?: string;
    authors?: string;
    link?: string;
    pdf_link?: string;
    summary?: string;
  };
  feedback?: "accept" | "reject";
}

export interface UserProfile {
  id: number;  
  name: string;
  email: string;
  picture?: string;
  user_id?: number; // Database user_id for backend operations
}

// New interfaces to match database structure
export interface DatabaseUser {
  user_id: number;
  name: string;
  email: string;
}

export interface DatabaseProject {
  project_id: number;
  user_id: number;
  topic: string;
  objective: string;
  guidelines: string;
}

export interface DatabaseQuery {
  query_id: number;
  project_id: number;
  queries_text: string;
  special_instructions: string;
}

export interface DatabasePaper {
  paper_id: number;
  project_id: number;
  query_id: number | null;
  paper_title: string;
  paper_summary: string;
  published_year: number | null;
  pdf_link: string | null;
}

export interface DatabaseAuthor {
  author_id: number;
  name: string;
}

export interface DatabasePaperWithAuthors extends DatabasePaper {
  authors: DatabaseAuthor[];
}

export interface DatabaseYoutube {
  youtube_id: number;
  project_id: number;
  query_id: number | null;
  video_title: string;
  video_description: string;
  video_duration: string | null;  // TIME converted to string
  video_url: string | null;
  video_views: number;
  video_likes: number;
}

export interface DatabaseLike {
  liked_disliked_id: number;
  project_id: number;
  target_type: "youtube" | "paper";
  target_id: number;
  isLiked: boolean;
}

export interface CompleteProjectData {
  project: DatabaseProject;
  queries: DatabaseQuery[];
  papers: DatabasePaperWithAuthors[];
  youtube_videos: DatabaseYoutube[];
  likes: DatabaseLike[];
}