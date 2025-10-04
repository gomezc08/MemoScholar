import { useState } from "react";
import { Download, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { HeaderBar } from "@/components/ui/header_bar";
import { ManagementPanel } from "@/components/ui/management_panel";
import SimpleLogin from "@/components/ui/simple-login";
import { updateLikeStatus } from "@/lib/api";
import type { Item, UserProfile } from "@/types";

interface HomeScreenProps {
  topic: string;
  objective: string;
  guidelines: string;
  youtubeItems: Item[];
  paperItems: Item[];
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
  onBackToSetup,
  user,
  onUserLogin,
  onUserLogout
}: HomeScreenProps) {
  const [isManagementOpen, setIsManagementOpen] = useState(false);
  const [likedItems, setLikedItems] = useState<Item[]>([]);
  const [dislikedItems, setDislikedItems] = useState<Item[]>([]);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const onSavePDF = () => window.print();
  
  const handleBackToSetup = () => {
    setShowConfirmDialog(true);
  };
  
  const confirmBackToSetup = () => {
    setShowConfirmDialog(false);
    onBackToSetup();
  };

  const handleItemFeedback = (item: Item, feedback: 'accept' | 'reject') => {
    const updatedItem = { ...item, feedback };
    
    if (feedback === 'accept') {
      // Remove from disliked if it exists there
      setDislikedItems(prev => prev.filter(i => i.id !== item.id));
      // Add to liked if not already there
      setLikedItems(prev => {
        const exists = prev.some(i => i.id === item.id);
        return exists ? prev : [...prev, updatedItem];
      });
    } else {
      // Remove from liked if it exists there
      setLikedItems(prev => prev.filter(i => i.id !== item.id));
      // Add to disliked if not already there
      setDislikedItems(prev => {
        const exists = prev.some(i => i.id === item.id);
        return exists ? prev : [...prev, updatedItem];
      });
    }
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
      setLikedItems(prev => [...prev, updatedItem]);
    } else {
      setDislikedItems(prev => [...prev, updatedItem]);
    }

    // Call backend API to update the database
    try {
      const payload = {
        liked_disliked_id: item.liked_disliked_id
      };
      
      console.log("Calling updateLikeStatus API with payload:", payload);
      const result = await updateLikeStatus(payload);
      console.log("Like status updated:", result);
    } catch (error) {
      console.error("Error updating like status:", error);
      
      // Revert UI state on error
      if (fromType === 'liked') {
        setLikedItems(prev => [...prev, item]);
        setDislikedItems(prev => prev.filter(item => item.id !== id));
      } else {
        setDislikedItems(prev => [...prev, item]);
        setLikedItems(prev => prev.filter(item => item.id !== id));
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
              items={youtubeItems}
              onItemFeedback={handleItemFeedback}
              user={user}
            />
          </div>
          <div className="flex-1">
            <Panel 
              kind="paper" 
              topic={topic} 
              objective={objective} 
              guidelines={guidelines}
              items={paperItems}
              onItemFeedback={handleItemFeedback}
              user={user}
            />
          </div>
        </div>
      </main>

      <Button onClick={onSavePDF} className="fixed bottom-5 right-5 shadow-lg" size="lg">
        <Download className="h-4 w-4 mr-2" /> Save as PDF
      </Button>

      <ManagementPanel
        isOpen={isManagementOpen}
        onClose={() => setIsManagementOpen(false)}
        likedItems={likedItems}
        dislikedItems={dislikedItems}
        onRemoveItem={handleRemoveItem}
        onMoveItem={handleMoveItem}
      />

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-zinc-900 p-6 rounded-lg shadow-xl border border-zinc-800 max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-pink-500" />
              <h3 className="text-lg font-semibold text-white">Confirm Action</h3>
            </div>
            <p className="text-zinc-300 mb-6">
              Are you sure you want to go back to setup? All your current work including liked/disliked items will be lost and you'll need to regenerate the content.
            </p>
            <div className="flex gap-3 justify-end">
              <Button 
                variant="outline" 
                onClick={() => setShowConfirmDialog(false)}
                className="hover:border-pink-500"
              >
                Cancel
              </Button>
              <Button 
                onClick={confirmBackToSetup}
                className="bg-pink-500 hover:bg-pink-600 hover:border-pink-500"
              >
                Yes, Go Back
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
