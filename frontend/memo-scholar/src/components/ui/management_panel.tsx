import { useState } from "react";
import { X, Heart, ThumbsDown, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Item } from "@/types";

interface ManagementPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
  likedItems: Item[];
  dislikedItems: Item[];
  onRemoveItem: (id: string, type: 'liked' | 'disliked') => void;
}

export function ManagementPanel({ 
  isOpen, 
  onClose, 
  isDark, 
  likedItems, 
  dislikedItems, 
  onRemoveItem 
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
    <Card key={item.id} className={`mb-3 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm mb-1 truncate">{item.title}</h4>
            <p className="text-xs text-muted-foreground mb-2">{formatMeta(item)}</p>
            <Badge variant={type === 'liked' ? 'default' : 'destructive'} className="text-xs">
              {type === 'liked' ? 'Liked' : 'Disliked'}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onRemoveItem(item.id, type)}
            className="ml-2 h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
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
        } ${isDark ? 'bg-black/50' : 'bg-black/30'}`}
        onClick={onClose}
      />
      
      {/* Panel */}
      <div 
        className={`fixed left-0 top-0 h-full w-1/3 z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } ${isDark ? 'bg-gray-900/95' : 'bg-white/95'} backdrop-blur-md border-r ${
          isDark ? 'border-gray-700' : 'border-gray-200'
        }`}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className={`p-4 border-b ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Manage Items</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Tabs */}
            <div className="flex mt-4 space-x-1">
              <Button
                variant={activeTab === 'liked' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab('liked')}
                className="flex-1"
              >
                <Heart className="h-4 w-4 mr-2" />
                Liked ({likedItems.length})
              </Button>
              <Button
                variant={activeTab === 'disliked' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab('disliked')}
                className="flex-1"
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
                  <div className="text-center py-8 text-muted-foreground">
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
                  <div className="text-center py-8 text-muted-foreground">
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
