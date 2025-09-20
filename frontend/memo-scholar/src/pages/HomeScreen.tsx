import { useState } from "react";
import { Download, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { HeaderBar } from "@/components/ui/header_bar";
import { ManagementPanel } from "@/components/ui/management_panel";
import type { Item } from "@/types";

interface HomeScreenProps {
  topic: string;
  objective: string;
  guidelines: string;
  youtubeItems: Item[];
  paperItems: Item[];
  onBackToSetup: () => void;
}

export default function HomeScreen({ 
  topic, 
  objective, 
  guidelines, 
  youtubeItems, 
  paperItems, 
  onBackToSetup 
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

  const handleRemoveItem = (id: string, type: 'liked' | 'disliked') => {
    if (type === 'liked') {
      setLikedItems(prev => prev.filter(item => item.id !== id));
    } else {
      setDislikedItems(prev => prev.filter(item => item.id !== id));
    }
  };

  const handleMoveItem = (id: string, fromType: 'liked' | 'disliked', toType: 'liked' | 'disliked') => {
    // Find the item to move
    const sourceList = fromType === 'liked' ? likedItems : dislikedItems;
    const item = sourceList.find(item => item.id === id);
    
    if (!item) return;

    // Update the item's feedback status
    const updatedItem = { ...item, feedback: toType === 'liked' ? 'accept' as const : 'reject' as const };

    // Remove from source list
    if (fromType === 'liked') {
      setLikedItems(prev => prev.filter(item => item.id !== id));
    } else {
      setDislikedItems(prev => prev.filter(item => item.id !== id));
    }

    // Add to target list
    if (toType === 'liked') {
      setLikedItems(prev => [...prev, updatedItem]);
    } else {
      setDislikedItems(prev => [...prev, updatedItem]);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      <HeaderBar 
        onManageClick={() => setIsManagementOpen(true)} 
      />

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
                <span className="text-2xl">🧠</span>
                <h1 className="text-xl font-bold text-white">{topic}</h1>
              </div>
            </div>

            {/* Project details with emojis */}
            <div className="space-y-4 pr-24">
              <div className="flex items-start gap-3">
                <span className="text-lg">🎯</span>
                <div>
                  <label className="text-sm font-medium text-zinc-400">Objective</label>
                  <p className="text-white mt-1">{objective}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-lg">📋</span>
                <div>
                  <label className="text-sm font-medium text-zinc-400">Guidelines</label>
                  <p className="text-white mt-1 whitespace-pre-wrap">{guidelines}</p>
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
