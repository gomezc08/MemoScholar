import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { HeaderBar } from "@/components/ui/header_bar";
import { ManagementPanel } from "@/components/ui/management_panel";
import SimpleLogin from "@/components/ui/simple-login";
import { updateLikeStatus, getProjectLikes, getYoutubeVideo, getPaper } from "@/lib/api";
import type { Item, UserProfile } from "@/types";

interface HomeScreenProps {
  topic: string;
  objective: string;
  guidelines: string;
  youtubeItems: Item[];
  paperItems: Item[];
  project_id: number;
  query_id: number;
  onBackToSetup: () => void;
  onItemsUpdate?: (youtubeItems: Item[], paperItems: Item[]) => void;
  user: UserProfile | null;
  onUserLogin: (user: UserProfile) => void;
  onUserLogout: () => void;
}

export default function HomeScreen({ 
  topic, 
  objective, 
  guidelines, 
  youtubeItems, 
  paperItems, 
  project_id,
  query_id,
  onBackToSetup,
  onItemsUpdate,
  user,
  onUserLogin,
  onUserLogout
}: HomeScreenProps) {
  const [isManagementOpen, setIsManagementOpen] = useState(false);
  const [likedItems, setLikedItems] = useState<Item[]>([]);
  const [dislikedItems, setDislikedItems] = useState<Item[]>([]);
  const [] = useState(false);

  // Helper to build a stable composite identity across types
  const getItemKey = (it: Item) => `${it.target_type || 'unknown'}-${it.database_id ?? it.id}`;

  // Rebuild liked/disliked lists from server likes
  const rebuildFromLikes = async () => {
    try {
      console.log(`🔄 Starting rebuildFromLikes for project_id: ${project_id}`);
      const likes = await getProjectLikes(project_id);
      console.log(`📊 Raw likes from server:`, likes);
      // Keep only the latest like per target
      const latestByKey = new Map<string, any>();
      for (const like of likes) {
        const key = `${like.target_type}-${like.target_id}`;
        const prev = latestByKey.get(key);
        if (!prev || like.liked_disliked_id > prev.liked_disliked_id) {
          latestByKey.set(key, like);
        }
      }
      console.log(`📋 Latest likes by key:`, Array.from(latestByKey.entries()));
      console.log(`🔍 Looking for target_id: 48 in latestByKey:`, latestByKey.has('youtube-48'));

      const nextLiked: Item[] = [];
      const nextDisliked: Item[] = [];

      // Fetch each liked/disliked item from the database
      for (const [, like] of latestByKey) {
        try {
          let itemData: any = null;
          
          if (like.target_type === 'youtube') {
            console.log(`🔍 Trying to fetch YouTube video with target_id: ${like.target_id}`);
            
            // First, check if the video exists in the current youtubeItems prop
            // This handles the case where the video is from youtube_current_recs (regenerated videos)
            const existingItem = youtubeItems.find(item => item.database_id === like.target_id);
            if (existingItem) {
              console.log(`📺 Found video in current youtubeItems prop`);
              itemData = {
                video_title: existingItem.title,
                youtube_id: existingItem.database_id,
                project_id: existingItem.project_id,
                video_duration: existingItem.meta.duration,
                video_views: existingItem.meta.views,
                video_likes: existingItem.meta.likes,
                video_url: existingItem.meta.video_url
              };
            } else {
              // Try to get from youtube table (permanent videos)
              itemData = await getYoutubeVideo(like.target_id);
              console.log(`📺 Result from permanent youtube table:`, itemData ? 'Found' : 'Not found');
            }
            
            if (itemData) {
              // Convert database format to Item format
              const item: Item = {
                id: Date.now() + Math.random(), // Generate unique ID for display
                title: itemData.video_title,
                database_id: itemData.youtube_id,
                target_type: 'youtube' as const,
                project_id: itemData.project_id,
                meta: {
                  channel: "YouTube",
                  duration: itemData.video_duration,
                  views: parseInt(itemData.video_views) || 0,
                  likes: parseInt(itemData.video_likes) || 0,
                  video_url: itemData.video_url
                },
                feedback: like.isLiked ? 'accept' : 'reject',
                liked_disliked_id: like.liked_disliked_id
              };
              
              if (like.isLiked) {
                nextLiked.push(item);
              } else {
                nextDisliked.push(item);
              }
            } else {
              // If not found in youtube table, try youtube_current_recs table (regenerated videos)
              console.log(`🔍 Trying to fetch from youtube_current_recs table for rec_id: ${like.target_id}`);
              try {
                const recResponse = await fetch(`/api/youtube/rec/${like.target_id}`, {
                  method: "GET",
                  headers: { "Content-Type": "application/json" },
                });
                console.log(`📺 Rec API response status: ${recResponse.status}`);
                if (recResponse.ok) {
                  const recData = await recResponse.json();
                  console.log(`📺 Rec API response data:`, recData);
                  if (recData.success && recData.video) {
                    itemData = recData.video;
                    // Convert database format to Item format for rec data
                    const item: Item = {
                      id: Date.now() + Math.random(), // Generate unique ID for display
                      title: itemData.video_title,
                      database_id: itemData.rec_id, // Use rec_id for regenerated videos
                      target_type: 'youtube' as const,
                      project_id: itemData.project_id,
                      meta: {
                        channel: "YouTube",
                        duration: itemData.video_duration,
                        views: parseInt(itemData.video_views) || 0,
                        likes: parseInt(itemData.video_likes) || 0,
                        video_url: itemData.video_url,
                        score: itemData.score,
                        calculated_score: itemData.calculated_score,
                        rank_position: itemData.rank_position
                      },
                      feedback: like.isLiked ? 'accept' : 'reject',
                      liked_disliked_id: like.liked_disliked_id
                    };
                    
                    if (like.isLiked) {
                      nextLiked.push(item);
                    } else {
                      nextDisliked.push(item);
                    }
                  }
                }
              } catch (recError) {
                console.error(`Failed to fetch rec data for ${like.target_id}:`, recError);
              }
            }
          } else if (like.target_type === 'paper') {
            itemData = await getPaper(like.target_id);
            if (itemData) {
              // Convert database format to Item format
              const item: Item = {
                id: Date.now() + Math.random(), // Generate unique ID for display
                title: itemData.paper_title,
                database_id: itemData.paper_id,
                target_type: 'paper' as const,
                project_id: itemData.project_id,
                meta: {
                  venue: "ArXiv",
                  year: itemData.published_year,
                  authors: "Unknown", // We don't have authors in the basic paper data
                  link: itemData.pdf_link,
                  pdf_link: itemData.pdf_link,
                  summary: itemData.paper_summary
                },
                feedback: like.isLiked ? 'accept' : 'reject',
                liked_disliked_id: like.liked_disliked_id
              };
              
              if (like.isLiked) {
                nextLiked.push(item);
              } else {
                nextDisliked.push(item);
              }
            }
          }
        } catch (error) {
          console.error(`Failed to fetch ${like.target_type} item ${like.target_id}:`, error);
          // Continue with other items even if one fails
        }
      }

      // Dedupe by composite key
      const likedKeys = new Set(nextLiked.map(getItemKey));
      const finalDisliked = nextDisliked.filter(i => !likedKeys.has(getItemKey(i)));

      console.log(`📝 Setting liked items:`, nextLiked.map(item => ({ id: item.id, title: item.title, database_id: item.database_id })));
      console.log(`📝 Setting disliked items:`, finalDisliked.map(item => ({ id: item.id, title: item.title, database_id: item.database_id })));

      // Instead of completely replacing the state, merge with existing state
      // This prevents the rebuild from overriding immediate state updates
      setLikedItems(prev => {
        const existingKeys = new Set(prev.map(getItemKey));
        const newItems = nextLiked.filter(item => !existingKeys.has(getItemKey(item)));
        return [...prev, ...newItems];
      });
      
      setDislikedItems(prev => {
        const existingKeys = new Set(prev.map(getItemKey));
        const newItems = finalDisliked.filter(item => !existingKeys.has(getItemKey(item)));
        return [...prev, ...newItems];
      });
    } catch (e) {
      console.error('Failed to sync likes from server:', e);
    }
  };

  // Single effect to handle server sync and item categorization
  useEffect(() => {
    // First, try to rebuild from server likes (this is the source of truth)
    console.log(`🔄 RebuildFromLikes triggered for project_id: ${project_id}`);
    rebuildFromLikes();
  }, [project_id]); // Only rebuild when project changes, not when items change

  // Also run rebuildFromLikes when youtubeItems change (when navigating back to conversation)
  useEffect(() => {
    if (youtubeItems.length > 0) {
      console.log(`🔄 RebuildFromLikes triggered because youtubeItems changed (${youtubeItems.length} items)`);
      rebuildFromLikes();
    }
  }, [youtubeItems]);

  // Show only items without feedback AND not already in liked/disliked lists
  // This ensures items don't appear in both panels and management panel
  const getLikedDislikedKeys = () => {
    const likedKeys = new Set(likedItems.map(getItemKey));
    const dislikedKeys = new Set(dislikedItems.map(getItemKey));
    const allKeys = new Set([...likedKeys, ...dislikedKeys]);
    console.log(`🔑 Current processed keys:`, Array.from(allKeys));
    return allKeys;
  };

  const alreadyProcessedKeys = getLikedDislikedKeys();
  console.log(`🔍 Current processed keys when filtering:`, Array.from(alreadyProcessedKeys));
  console.log(`🔍 YouTube items before filtering:`, youtubeItems.map(item => ({ 
    id: item.id, 
    title: item.title.substring(0, 30) + '...', 
    database_id: item.database_id, 
    key: getItemKey(item)
  })));
  
  const youtubeItemsWithoutFeedback = youtubeItems.filter(item => {
    const shouldShow = !item.feedback && !alreadyProcessedKeys.has(getItemKey(item));
    if (!shouldShow) {
      console.log(`🔍 Filtering out item "${item.title.substring(0, 30)}..." (key: ${getItemKey(item)})`);
    }
    return shouldShow;
  });
  
  const paperItemsWithoutFeedback = paperItems.filter(item => 
    !item.feedback && !alreadyProcessedKeys.has(getItemKey(item))
  );
  
  const handleBackToSetup = () => {
    onBackToSetup();
  };

  const handleItemFeedback = async (item: Item, feedback: 'accept' | 'reject') => {
    const key = getItemKey(item);
    
    // Update local state immediately for better UX
    if (feedback === 'accept') {
      // Remove from disliked if it exists there (by composite key)
      setDislikedItems(prev => prev.filter(i => getItemKey(i) !== key));
      // Add to liked if not already there (by composite key)
      setLikedItems(prev => {
        if (prev.some(i => getItemKey(i) === key)) return prev;
        return [...prev, { ...item, feedback }];
      });
    } else {
      // Remove from liked if it exists there (by composite key)
      setLikedItems(prev => prev.filter(i => getItemKey(i) !== key));
      // Add to disliked if not already there (by composite key)
      setDislikedItems(prev => {
        if (prev.some(i => getItemKey(i) === key)) return prev;
        return [...prev, { ...item, feedback }];
      });
    }

    // Sync from server after a short delay to ensure API call completes
    // This ensures the server state is the source of truth
    setTimeout(async () => {
      await rebuildFromLikes();
    }, 100);
  };

  const handleRemoveItem = (id: number, type: 'liked' | 'disliked') => {
    // Find the item to remove to get its composite key
    const sourceList = type === 'liked' ? likedItems : dislikedItems;
    const item = sourceList.find(item => item.id === id);
    
    if (!item) return;
    
    const key = getItemKey(item);
    
    if (type === 'liked') {
      setLikedItems(prev => prev.filter(i => getItemKey(i) !== key));
    } else {
      setDislikedItems(prev => prev.filter(i => getItemKey(i) !== key));
    }
  };

  const handleMoveItem = async (id: number, fromType: 'liked' | 'disliked', toType: 'liked' | 'disliked') => {
    // Find the item to move
    const sourceList = fromType === 'liked' ? likedItems : dislikedItems;
    const item = sourceList.find(item => item.id === id);
    
    if (!item) return;

    // Check if we have the required database information
    if (!item.liked_disliked_id) {
      console.error("Missing liked_disliked_id for item:", item);
      alert("This item is missing database information. Cannot update like status.");
      return;
    }

    // Update UI state immediately for visual feedback using composite keys
    const key = getItemKey(item);
    const updatedItem = { ...item, feedback: toType === 'liked' ? 'accept' as const : 'reject' as const };

    // Remove from source list using composite key
    if (fromType === 'liked') {
      setLikedItems(prev => prev.filter(i => getItemKey(i) !== key));
    } else {
      setDislikedItems(prev => prev.filter(i => getItemKey(i) !== key));
    }

    // Add to destination list using composite key
    if (toType === 'liked') {
      setLikedItems(prev => (prev.some(i => getItemKey(i) === key) ? prev : [...prev, updatedItem]));
    } else {
      setDislikedItems(prev => (prev.some(i => getItemKey(i) === key) ? prev : [...prev, updatedItem]));
    }

    // Call backend API to update the database
    try {
      const payload = {
        liked_disliked_id: item.liked_disliked_id
      };
      
      console.log("Calling updateLikeStatus API with payload:", payload);
      const result = await updateLikeStatus(payload);
      console.log("Like status updated:", result);

      // Sync from server after successful toggle with delay
      setTimeout(async () => {
        await rebuildFromLikes();
      }, 100);
    } catch (error) {
      console.error("Error updating like status:", error);
      
      // Revert UI state on error using composite keys
      if (fromType === 'liked') {
        setLikedItems(prev => (prev.some(i => getItemKey(i) === key) ? prev : [...prev, item]));
        setDislikedItems(prev => prev.filter(i => getItemKey(i) !== key));
      } else {
        setDislikedItems(prev => (prev.some(i => getItemKey(i) === key) ? prev : [...prev, item]));
        setLikedItems(prev => prev.filter(i => getItemKey(i) !== key));
      }
      
      alert("Failed to update like status. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      <HeaderBar 
        onManageClick={() => setIsManagementOpen(true)} 
      />
      
      {/* Simple Login Section */}
      <div className="w-full px-4 py-3 bg-zinc-900 border-b border-zinc-800">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-sm text-zinc-400">Welcome to MemoScholar</span>
            {user && (
              <span className="text-sm text-pink-400">
                • Signed in as {user.name}
              </span>
            )}
          </div>
          <SimpleLogin 
            onLogin={onUserLogin}
            onLogout={onUserLogout}
            user={user}
          />
        </div>
      </div>

      <main className="flex-1 w-full px-4 py-6 space-y-6">
        <div className="relative">
          <div className="p-6">
            <div className="absolute top-4 right-4">
              <Button onClick={handleBackToSetup} variant="outline" size="sm">
                ← Back to Setup
              </Button>
            </div>
            
            {/* Decorative border and title */}
            <div className="text-center mb-6 pr-24">
              <div className="flex items-center justify-center gap-2 mb-2">
                <span className="text-3xl">🧠</span>
                <h1 className="text-3xl font-bold text-white">{topic}</h1>
              </div>
            </div>

            {/* Project details with emojis */}
            <div className="space-y-4 pr-24">
              <div className="flex items-start gap-3">
                <span className="text-lg">🎯</span>
                <div>
                  <h2 className="text-base font-semibold text-zinc-300 mb-2">Objective</h2>
                  <p className="text-white">{objective}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg">📋</span>
                <div>
                  <h2 className="text-base font-semibold text-zinc-300 mb-2">Guidelines</h2>
                  <p className="text-white whitespace-pre-wrap">{guidelines}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col min-[600px]:flex-row gap-4">
          <div className="flex-1">
            <Panel 
              kind="youtube" 
              topic={topic} 
              objective={objective} 
              guidelines={guidelines}
              items={youtubeItemsWithoutFeedback}
              onItemFeedback={handleItemFeedback}
              onItemsUpdate={(newItems) => {
                if (onItemsUpdate) {
                  onItemsUpdate(newItems, paperItems);
                }
              }}
              user={user}
              project_id={project_id}
              query_id={query_id}
            />
          </div>
          <div className="flex-1">
            <Panel 
              kind="paper" 
              topic={topic} 
              objective={objective} 
              guidelines={guidelines}
              items={paperItemsWithoutFeedback}
              onItemFeedback={handleItemFeedback}
              onItemsUpdate={(newItems) => {
                if (onItemsUpdate) {
                  onItemsUpdate(youtubeItems, newItems);
                }
              }}
              user={user}
              project_id={project_id}
              query_id={query_id}
            />
          </div>
        </div>
      </main>

      <ManagementPanel
        isOpen={isManagementOpen}
        onClose={() => setIsManagementOpen(false)}
        likedItems={likedItems}
        dislikedItems={dislikedItems}
        onRemoveItem={handleRemoveItem}
        onMoveItem={handleMoveItem}
      />
    </div>
  );
}
