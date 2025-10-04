import { useState } from 'react';
import { Button } from './button';
import { Input } from './input';
import { LogOut, Mail, User } from 'lucide-react';
import type { UserProfile } from '@/types';

interface SimpleLoginProps {
  onLogin: (user: UserProfile) => void;
  onLogout: () => void;
  user: UserProfile | null;
}

export default function SimpleLogin({ onLogin, onLogout, user }: SimpleLoginProps) {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim() || !email.trim()) {
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      alert('Please enter a valid email address');
      return;
    }

    setIsLoading(true);
    
    // Simulate a brief loading state
    setTimeout(() => {
      const userProfile: UserProfile = {
        id: `user_${Date.now()}`,
        name: name.trim(),
        email: email.trim().toLowerCase(),
        picture: `https://ui-avatars.com/api/?name=${encodeURIComponent(name.trim())}&background=random&color=fff&size=32`
      };
      
      onLogin(userProfile);
      setIsLoginOpen(false);
      setName('');
      setEmail('');
      setIsLoading(false);
    }, 500);
  };

  const handleLogout = () => {
    onLogout();
  };

  if (user) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <img 
            src={user.picture} 
            alt={user.name}
            className="w-8 h-8 rounded-full"
          />
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-white">{user.name}</p>
            <p className="text-xs text-zinc-400">{user.email}</p>
          </div>
        </div>
        <Button
          onClick={handleLogout}
          variant="outline"
          size="sm"
          className="hover:border-pink-500"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {!isLoginOpen ? (
        <Button
          onClick={() => setIsLoginOpen(true)}
          variant="outline"
          className="flex items-center gap-2 bg-white text-gray-700 hover:bg-gray-50 border-gray-300"
        >
          <Mail className="h-4 w-4" />
          Sign In
        </Button>
      ) : (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-zinc-900 p-6 rounded-lg shadow-xl border border-zinc-800 max-w-md mx-4 w-full">
            <div className="flex items-center gap-3 mb-4">
              <User className="h-6 w-6 text-pink-500" />
              <h3 className="text-lg font-semibold text-white">Sign In to MemoScholar</h3>
            </div>
            
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300">Name</label>
                <Input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  className="bg-zinc-800 border-zinc-700 text-white"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-300">Email</label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="bg-zinc-800 border-zinc-700 text-white"
                  required
                />
              </div>
              
              <div className="flex gap-3 justify-end pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsLoginOpen(false);
                    setName('');
                    setEmail('');
                  }}
                  className="hover:border-pink-500"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading || !name.trim() || !email.trim()}
                  className="bg-pink-500 hover:bg-pink-600"
                >
                  {isLoading ? 'Signing In...' : 'Sign In'}
                </Button>
              </div>
            </form>
            
            <p className="text-xs text-zinc-500 mt-4 text-center">
              No password required. We'll use this to personalize your experience.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
