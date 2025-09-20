import { useState } from "react";
import { Download } from "lucide-react";
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

  const onSavePDF = () => window.print();

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
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white mb-2">Project Results</h2>
            <p className="text-zinc-400">Topic: {topic}</p>
            <p className="text-zinc-400">Objective: {objective}</p>
          </div>
          <Button onClick={onBackToSetup} variant="outline">
            ← Back to Setup
          </Button>
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
    </div>
  );
}
