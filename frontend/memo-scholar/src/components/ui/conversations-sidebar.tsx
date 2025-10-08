import { useState, useEffect } from 'react';
import { MessageSquare } from 'lucide-react';
import { Button } from './button';
import type { DatabaseProject, UserProfile } from '@/types';
import { getUserProjects } from '@/lib/api';

interface ConversationsSidebarProps {
  user: UserProfile | null;
  onProjectSelect: (project: DatabaseProject) => void;
  isHovered: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

export default function ConversationsSidebar({ 
  user, 
  onProjectSelect, 
  isHovered, 
  onMouseEnter, 
  onMouseLeave 
}: ConversationsSidebarProps) {
  const [projects, setProjects] = useState<DatabaseProject[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (user?.user_id) {
      loadUserProjects();
    } else {
      setProjects([]);
    }
  }, [user?.user_id]);

  const loadUserProjects = async () => {
    if (!user?.user_id) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      console.log('Loading projects for user_id:', user.user_id);
      const userProjects = await getUserProjects(user.user_id);
      console.log('Received projects:', userProjects);
      setProjects(userProjects);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  };

  const formatProjectTitle = (topic: string) => {
    // Truncate long topics and add ellipsis
    if (topic.length > 30) {
      return topic.substring(0, 30) + '...';
    }
    return topic;
  };


  return (
    <div 
      className={`fixed top-16 left-0 w-80 bg-zinc-900 border-r border-zinc-800 shadow-xl transition-all duration-300 z-50 ${
        isHovered ? 'translate-x-0 opacity-100' : '-translate-x-full opacity-0'
      }`}
      style={{ height: 'calc(100vh - 4rem)' }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Header */}
      <div className="p-4 border-b border-zinc-800">
        <h2 className="text-lg font-semibold text-white">Past Conversations</h2>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto px-4 pb-4" style={{ height: 'calc(100% - 8rem)' }}>
        {isLoading && (
          <div className="text-center py-8">
            <div className="text-zinc-400">Loading conversations...</div>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <div className="text-red-400 text-sm">{error}</div>
            <Button
              onClick={loadUserProjects}
              variant="outline"
              size="sm"
              className="mt-2"
            >
              Retry
            </Button>
          </div>
        )}

        {!isLoading && !error && projects.length === 0 && (
          <div className="text-center py-8">
            <MessageSquare className="h-12 w-12 text-zinc-600 mx-auto mb-4" />
            <div className="text-zinc-400 text-sm">No conversations yet</div>
            <div className="text-zinc-500 text-xs mt-1">
              Start a new project to see your conversations here
            </div>
          </div>
        )}

        {!isLoading && !error && projects.length > 0 && (
          <div className="space-y-2">
            {projects.map((project) => (
              <div
                key={project.project_id}
                onClick={() => onProjectSelect(project)}
                className="p-3 rounded-lg bg-zinc-800 hover:bg-zinc-700 cursor-pointer transition-colors group border border-zinc-700 hover:border-zinc-600"
              >
                <div className="flex items-start gap-3">
                  <MessageSquare className="h-4 w-4 text-zinc-400 group-hover:text-pink-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-white group-hover:text-pink-100 truncate">
                      {formatProjectTitle(project.topic)}
                    </h3>
                    <p className="text-xs text-zinc-400 mt-1 overflow-hidden" style={{ 
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {project.objective}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-zinc-800">
        <div className="text-xs text-zinc-500 text-center">
          {user ? `Signed in as ${user.name}` : 'Not signed in'}
        </div>
      </div>
    </div>
  );
}
