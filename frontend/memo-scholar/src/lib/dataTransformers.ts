import type { Item, PanelKind } from '../types';
import type { 
  DatabasePaperWithAuthors, 
  DatabaseYoutube, 
  DatabaseLike,
  CompleteProjectData 
} from '../types';

/**
 * Transform database paper data to frontend Item format
 */
export function transformPaperToItem(paper: DatabasePaperWithAuthors): Item {
  // Concatenate author names into a single string
  const authorsString = paper.authors
    .map(author => author.name)
    .join(', ');

  return {
    id: paper.paper_id,
    title: paper.paper_title,
    meta: {
      venue: '', // Not in database schema, will be empty
      year: paper.published_year || undefined,
      authors: authorsString || undefined,
      pdf_link: paper.pdf_link || undefined,
      summary: paper.paper_summary || undefined,
      score: (paper as any).score,
      calculated_score: (paper as any).calculated_score,
      rank_position: (paper as any).rank_position,
    },
    feedback: undefined, // Will be set based on likes data
  };
}

/**
 * Transform database YouTube data to frontend Item format
 */
export function transformYoutubeToItem(youtube: DatabaseYoutube): Item {
  return {
    id: youtube.youtube_id,
    title: youtube.video_title,
    meta: {
      channel: '', // Not in database schema, will be empty
      duration: youtube.video_duration || undefined,
      views: youtube.video_views,
      likes: youtube.video_likes,
      video_url: youtube.video_url || undefined,
      score: youtube.score,
      calculated_score: youtube.calculated_score,
      rank_position: youtube.rank_position,
    },
    feedback: undefined, // Will be set based on likes data
  };
}

/**
 * Apply like/dislike feedback to items based on likes data
 */
export function applyFeedbackToItems(
  items: Item[], 
  likes: DatabaseLike[], 
  panelKind: PanelKind
): Item[] {
  return items.map(item => {
    // Find likes for this specific item
    const itemLikes = likes.filter(like => 
      like.target_type === panelKind && 
      like.target_id === item.id
    );

    // If there are likes, determine the overall feedback
    let feedback: "accept" | "reject" | undefined = undefined;
    
    if (itemLikes.length > 0) {
      // For now, use the most recent like as the feedback
      // You might want to implement more sophisticated logic here
      const latestLike = itemLikes[itemLikes.length - 1];
      feedback = latestLike.isLiked ? "accept" : "reject";
    }

    return {
      ...item,
      feedback,
    };
  });
}

/**
 * Transform complete project data to frontend format
 */
export function transformProjectDataToFrontend(data: CompleteProjectData) {
  // Transform papers
  const paperItems = data.papers.map(transformPaperToItem);
  const paperItemsWithFeedback = applyFeedbackToItems(paperItems, data.likes, 'paper');

  // Transform YouTube videos
  const youtubeItems = data.youtube_videos.map(transformYoutubeToItem);
  const youtubeItemsWithFeedback = applyFeedbackToItems(youtubeItems, data.likes, 'youtube');

  return {
    project: data.project,
    queries: data.queries,
    papers: paperItemsWithFeedback,
    youtube: youtubeItemsWithFeedback,
    likes: data.likes,
  };
}

/**
 * Helper function to format numbers for display (e.g., 1000 -> "1K")
 */
export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

/**
 * Helper function to format duration from database TIME format
 */
export function formatDuration(duration: string | null): string {
  if (!duration) return '';
  
  // Convert "HH:MM:SS" to more readable format
  const parts = duration.split(':');
  const hours = parseInt(parts[0]);
  const minutes = parseInt(parts[1]);
  const seconds = parseInt(parts[2]);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Helper function to get display text for feedback
 */
export function getFeedbackText(feedback: "accept" | "reject" | undefined): string {
  switch (feedback) {
    case 'accept':
      return '✅ Accepted';
    case 'reject':
      return '❌ Rejected';
    default:
      return '⏳ Pending';
  }
}

/**
 * Helper function to get feedback color for UI
 */
export function getFeedbackColor(feedback: "accept" | "reject" | undefined): string {
  switch (feedback) {
    case 'accept':
      return 'text-green-600';
    case 'reject':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}
