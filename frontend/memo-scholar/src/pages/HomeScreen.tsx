import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { HeaderBar } from "@/components/ui/header_bar";
import { ManagementPanel } from "@/components/ui/management_panel";
import SimpleLogin from "@/components/ui/simple-login";
import { updateLikeStatus, getProjectLikes } from "@/lib/api";
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
      const likes = await getProjectLikes(project_id);
      // Keep only the latest like per target
      const latestByKey = new Map<string, any>();
      for (const like of likes) {
        const key = `${like.target_type}-${like.target_id}`;
        const prev = latestByKey.get(key);
        if (!prev || like.liked_disliked_id > prev.liked_disliked_id) {
          latestByKey.set(key, like);
        }
      }

      const sourceItems = [...youtubeItems, ...paperItems];
      const nextLiked: Item[] = [];
      const nextDisliked: Item[] = [];

      for (const [, like] of latestByKey) {
        const item = sourceItems.find(i => (i.target_type === like.target_type) && ((i.database_id ?? i.id) === like.target_id));
        if (item) {
          const updated: Item = { ...item, feedback: like.isLiked ? 'accept' : 'reject', liked_disliked_id: like.liked_disliked_id };
          if (updated.feedback === 'accept') nextLiked.push(updated); else nextDisliked.push(updated);
        }
      }

      // Dedupe by composite key
      const likedKeys = new Set(nextLiked.map(getItemKey));
      const finalDisliked = nextDisliked.filter(i => !likedKeys.has(getItemKey(i)));

      setLikedItems(nextLiked);
      setDislikedItems(finalDisliked);
    } catch (e) {
      console.error('Failed to sync likes from server:', e);
    }
  };

  // Initial and project/content change sync
  useEffect(() => {
    rebuildFromLikes();
  }, [project_id, youtubeItems, paperItems]);

  // Populate liked and disliked items from the passed data
  useEffect(() => {
    const liked: Item[] = [];
    const disliked: Item[] = [];

    console.log('Categorizing items - YouTube items:', youtubeItems);
    console.log('Categorizing items - Paper items:', paperItems);

    // Check YouTube items
    youtubeItems.forEach(item => {
      console.log(`YouTube item ${item.database_id}: feedback=${item.feedback}`);
      if (item.feedback === 'accept') {
        liked.push(item);
      } else if (item.feedback === 'reject') {
        disliked.push(item);
      }
    });

    // Check Paper items
    paperItems.forEach(item => {
      console.log(`Paper item ${item.database_id}: feedback=${item.feedback}`);
      if (item.feedback === 'accept') {
        liked.push(item);
      } else if (item.feedback === 'reject') {
        disliked.push(item);
      }
    });

    console.log('Final liked items:', liked.map(i => `${i.database_id}:${i.feedback}`));
    console.log('Final disliked items:', disliked.map(i => `${i.database_id}:${i.feedback}`));

    // Ensure no item appears in both arrays (safety check) using composite keys
    const likedKeys = new Set(liked.map(getItemKey));
    const finalDisliked = disliked.filter(i => !likedKeys.has(getItemKey(i)));
    
    console.log('After deduplication - liked:', liked.length, 'disliked:', finalDisliked.length);

    setLikedItems(liked);
    setDislikedItems(finalDisliked);
  }, [youtubeItems, paperItems]);

  // Show only items without feedback based on incoming item.feedback
  // This avoids wiping regenerated items due to external liked/disliked state
  const youtubeItemsWithoutFeedback = youtubeItems.filter(item => !item.feedback);
  const paperItemsWithoutFeedback = paperItems.filter(item => !item.feedback);
  
  const handleBackToSetup = () => {
    onBackToSetup();
  };

  const handleItemFeedback = async (item: Item, feedback: 'accept' | 'reject') => {
    const updatedItem = { ...item, feedback };
    const key = getItemKey(item);
    
    if (feedback === 'accept') {
      // Remove from disliked if it exists there (by composite key)
      setDislikedItems(prev => prev.filter(i => getItemKey(i) !== key));
      // Add to liked if not already there (by composite key)
      setLikedItems(prev => (prev.some(i => getItemKey(i) === key) ? prev : [...prev, updatedItem]));
    } else {
      // Remove from liked if it exists there (by composite key)
      setLikedItems(prev => prev.filter(i => getItemKey(i) !== key));
      // Add to disliked if not already there (by composite key)
      setDislikedItems(prev => (prev.some(i => getItemKey(i) === key) ? prev : [...prev, updatedItem]));
    }

    // Sync from server to ensure state matches DB
    await rebuildFromLikes();
  };

  const handleRemoveItem = (id: number, type: 'liked' | 'disliked') => {
    if (type === 'liked') {
      setLikedItems(prev => prev.filter(item => item.id !== id));
    } else {
      setDislikedItems(prev => prev.filter(item => item.id !== id));
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

    // Update the item's feedback status
    const updatedItem = { ...item, feedback: toType === 'liked' ? 'accept' as const : 'reject' as const };

    // Update UI state immediately for visual feedback
    if (fromType === 'liked') {
      setLikedItems(prev => prev.filter(item => item.id !== id));
    } else {
      setDislikedItems(prev => prev.filter(item => item.id !== id));
    }

    if (toType === 'liked') {
      setLikedItems(prev => (prev.some(i => getItemKey(i) === getItemKey(updatedItem)) ? prev : [...prev, updatedItem]));
    } else {
      setDislikedItems(prev => (prev.some(i => getItemKey(i) === getItemKey(updatedItem)) ? prev : [...prev, updatedItem]));
    }

    // Call backend API to update the database
    try {
      const payload = {
        liked_disliked_id: item.liked_disliked_id
      };
      
      console.log("Calling updateLikeStatus API with payload:", payload);
      const result = await updateLikeStatus(payload);
      console.log("Like status updated:", result);

      // Sync from server after successful toggle
      await rebuildFromLikes();
    } catch (error) {
      console.error("Error updating like status:", error);
      
      // Revert UI state on error
      if (fromType === 'liked') {
        setLikedItems(prev => (prev.some(i => getItemKey(i) === getItemKey(item)) ? prev : [...prev, item]));
        setDislikedItems(prev => prev.filter(it => it.id !== id));
      } else {
        setDislikedItems(prev => (prev.some(i => getItemKey(i) === getItemKey(item)) ? prev : [...prev, item]));
        setLikedItems(prev => prev.filter(it => it.id !== id));
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
