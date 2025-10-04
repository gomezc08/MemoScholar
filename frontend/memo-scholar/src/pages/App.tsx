import { useState, useEffect } from "react";
import Project from "./Project";
import HomeScreen from "./HomeScreen";
import type { Item, UserProfile } from "@/types";

export default function App() {
  const [hasRun, setHasRun] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [projectData, setProjectData] = useState<{
    topic: string;
    objective: string;
    guidelines: string;
    youtubeItems: Item[];
    paperItems: Item[];
  } | null>(null);

  // Load user from localStorage on app start
  useEffect(() => {
    const savedUser = localStorage.getItem('memoScholarUser');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('memoScholarUser');
      }
    }
  }, []);

  // Save user to localStorage when it changes
  useEffect(() => {
    if (user) {
      localStorage.setItem('memoScholarUser', JSON.stringify(user));
    } else {
      localStorage.removeItem('memoScholarUser');
    }
  }, [user]);

  const handleProjectComplete = (topic: string, objective: string, guidelines: string, youtubeItems: Item[], paperItems: Item[]) => {
    setProjectData({
      topic,
      objective,
      guidelines,
      youtubeItems,
      paperItems
    });
    setHasRun(true);
  };

  const handleBackToSetup = () => {
    setHasRun(false);
    setProjectData(null);
  };

  const handleUserLogin = (userProfile: UserProfile) => {
    setUser(userProfile);
  };

  const handleUserLogout = () => {
    setUser(null);
  };

  if (!hasRun || !projectData) {
    return <Project onProjectComplete={handleProjectComplete} user={user} onUserLogin={handleUserLogin} onUserLogout={handleUserLogout} />;
  }

  return (
    <HomeScreen
      topic={projectData.topic}
      objective={projectData.objective}
      guidelines={projectData.guidelines}
      youtubeItems={projectData.youtubeItems}
      paperItems={projectData.paperItems}
      onBackToSetup={handleBackToSetup}
      user={user}
      onUserLogin={handleUserLogin}
      onUserLogout={handleUserLogout}
    />
  );
}
