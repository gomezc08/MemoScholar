import { Button } from "@/components/ui/button";
import { Sun, Moon } from "lucide-react";

export function HeaderBar({ isDark, onToggle }: { isDark: boolean; onToggle: () => void }) {
  return (
    <header className={`sticky top-0 z-20 backdrop-blur border-b ${isDark ? "bg-gray-900/80" : "bg-white/80"}`}>
      <div className="w-full px-4 py-4">
        <div className="grid grid-cols-3 items-center">
          <div />
          <h1 className="text-center text-2xl sm:text-3xl font-semibold tracking-tight">MemoScholar</h1>
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={onToggle}>
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
