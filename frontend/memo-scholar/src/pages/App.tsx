import { useState } from "react";
import Project from "./Project";
import HomeScreen from "./HomeScreen";
import type { Item } from "@/types";

export default function App() {
  const [hasRun, setHasRun] = useState(false);
  const [projectData, setProjectData] = useState<{
    topic: string;
    objective: string;
    guidelines: string;
    youtubeItems: Item[];
    paperItems: Item[];
  } | null>(null);

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

  if (!hasRun || !projectData) {
    return <Project onProjectComplete={handleProjectComplete} />;
  }

  return (
    <HomeScreen
      topic={projectData.topic}
      objective={projectData.objective}
      guidelines={projectData.guidelines}
      youtubeItems={projectData.youtubeItems}
      paperItems={projectData.paperItems}
      onBackToSetup={handleBackToSetup}
    />
  );
}
