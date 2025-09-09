import { Button } from "@/components/ui/button";
import { Sun, Moon, Filter } from "lucide-react";

export function HeaderBar({ 
  isDark, 
  onToggle, 
  onManageClick 
}: { 
  isDark: boolean; 
  onToggle: () => void;
  onManageClick: () => void;
}) {
  return (
    <header className={`sticky top-0 z-20 backdrop-blur border-b ${isDark ? "bg-gray-900/80" : "bg-white/80"}`}>
      <div className="w-full px-4 py-4">
        <div className="grid grid-cols-3 items-center">
          <div />
          <h1 className="text-center text-3xl sm:text-4xl font-semibold tracking-tight">MemoScholar</h1>
          <div className="flex items-center justify-end gap-2">
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-12 w-12" 
              aria-label="Manage items" 
              onClick={onManageClick}
            >
              <Filter className="h-6 w-6" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              className={`h-12 w-12 ${isDark ? 'border-white' : 'border-black'} border-2`} 
              aria-label="Toggle theme" 
              onClick={onToggle}
            >
              {isDark ? <Sun className="h-10 w-10" /> : <Moon className="h-10 w-10" />}
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
