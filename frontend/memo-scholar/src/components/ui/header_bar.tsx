import { Button } from "@/components/ui/button";
import { Filter } from "lucide-react";

export function HeaderBar({ 
  onManageClick 
}: { 
  onManageClick?: () => void;
}) {
  return (
    <header className="sticky top-0 z-20 backdrop-blur border-b bg-zinc-900/80 border-zinc-800">
      <div className="w-full px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-white">MemoScholar</h1>
          {onManageClick && (
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-12 w-12 border-white border-2" 
              aria-label="Manage items" 
              onClick={onManageClick}
            >
              <Filter className="h-6 w-6" />
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
