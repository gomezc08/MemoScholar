import { useState } from "react";
import { X, Heart, ThumbsDown, Trash2, ArrowRightLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Item } from "@/types";

interface ManagementPanelProps {
  isOpen: boolean;
  onClose: () => void;
  likedItems: Item[];
  dislikedItems: Item[];
  onRemoveItem: (id: number, type: 'liked' | 'disliked') => void;
  onMoveItem: (id: number, fromType: 'liked' | 'disliked', toType: 'liked' | 'disliked') => void;
}

export function ManagementPanel({ 
  isOpen, 
  onClose, 
  likedItems, 
  dislikedItems, 
  onRemoveItem,
  onMoveItem
}: ManagementPanelProps) {
  const [activeTab, setActiveTab] = useState<'liked' | 'disliked'>('liked');

  const formatMeta = (item: Item) => {
    const meta = item.meta;
    if (item.feedback === 'accept') {
      return meta.channel ? `${meta.channel} • ${meta.duration}` : 
             meta.venue ? `${meta.venue} • ${meta.year}` : 
             meta.framework ? `${meta.framework} • ${meta.vram}` : '';
    }
    return '';
  };

  const renderItem = (item: Item, type: 'liked' | 'disliked') => (
    <Card key={item.id} className="mb-3 transition-all duration-200 bg-zinc-900/60 shadow-xl shadow-black border-zinc-800/50">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm mb-1 truncate text-white">{item.title}</h4>
            <p className="text-xs text-zinc-400 mb-2">{formatMeta(item)}</p>
            <Badge variant={type === 'liked' ? 'default' : 'destructive'} className="text-xs">
              {type === 'liked' ? 'Liked' : 'Disliked'}
            </Badge>
          </div>
          <div className="flex items-center gap-1 ml-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onMoveItem(item.id, type, type === 'liked' ? 'disliked' : 'liked')}
              className="h-8 w-8 p-0 text-zinc-700 hover:text-blue-500 transition-colors rounded-full"
              title={`Move to ${type === 'liked' ? 'Disliked' : 'Liked'}`}
            >
              <ArrowRightLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemoveItem(item.id, type)}
              className="h-8 w-8 p-0 text-zinc-700 hover:text-destructive transition-colors rounded-full"
              title="Remove item"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 z-40 transition-opacity duration-300 ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        } bg-black/50`}
        onClick={onClose}
      />
      
      {/* Panel */}
      <div 
        className={`fixed left-0 top-0 h-full w-1/3 z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } bg-zinc-900/95 backdrop-blur-md border-r border-zinc-800`}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-zinc-800">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Manage Items</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-8 w-8 p-0 rounded-full"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Tabs */}
            <div className="flex mt-4 space-x-1">
              <Button
                variant={activeTab === 'liked' ? 'default' : 'ghost'}
                className={`flex-1 ${activeTab === 'liked' ? 'bg-zinc-700' : 'text-zinc-700 hover:bg-zinc-700'}`}
                size="sm"
                onClick={() => setActiveTab('liked')}
              >
                <Heart className="h-4 w-4 mr-2" />
                Liked ({likedItems.length})
              </Button>
              <Button
                variant={activeTab === 'disliked' ? 'default' : 'ghost'}
                className={`flex-1 ${activeTab === 'disliked' ? 'bg-zinc-700' : 'text-zinc-700 hover:bg-zinc-700'}`}
                size="sm"
                onClick={() => setActiveTab('disliked')}
              >
                <ThumbsDown className="h-4 w-4 mr-2" />
                Disliked ({dislikedItems.length})
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === 'liked' ? (
              <div>
                {likedItems.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400">
                    <Heart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No liked items yet</p>
                    <p className="text-sm">Items you like will appear here</p>
                  </div>
                ) : (
                  likedItems.map(item => renderItem(item, 'liked'))
                )}
              </div>
            ) : (
              <div>
                {dislikedItems.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400">
                    <ThumbsDown className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No disliked items yet</p>
                    <p className="text-sm">Items you dislike will appear here</p>
                  </div>
                ) : (
                  dislikedItems.map(item => renderItem(item, 'disliked'))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
