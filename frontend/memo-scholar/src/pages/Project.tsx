import { useState } from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { HeaderBar } from "@/components/ui/header_bar";
import SimpleLogin from "@/components/ui/simple-login";
import ConversationsSidebar from "@/components/ui/conversations-sidebar";
import { generateSubmission, getCompleteProjectData } from "@/lib/api";
import type { Item, UserProfile, DatabaseProject } from "@/types";

interface ProjectProps {
  onProjectComplete: (topic: string, objective: string, guidelines: string, youtubeItems: Item[], paperItems: Item[], project_id: number, query_id: number) => void;
  user: UserProfile | null;
  onUserLogin: (user: UserProfile) => void;
  onUserLogout: () => void;
}

export default function Project({ onProjectComplete, user, onUserLogin, onUserLogout }: ProjectProps) {
  const [topic, setTopic] = useState("");
  const [objective, setObjective] = useState("");
  const [guidelines, setGuidelines] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [validationError, setValidationError] = useState<string>("");
  const [isSidebarHovered, setIsSidebarHovered] = useState(false);

  const handleProjectSelect = async (project: DatabaseProject) => {
    // Load the complete project data and navigate to the next screen
    try {
      const completeData = await getCompleteProjectData(project.project_id);
      
      // Transform YouTube videos to Item format
      const youtubeItems: Item[] = completeData.youtube_videos.map((video: any) => ({
        id: video.youtube_id,
        title: video.video_title,
        database_id: video.youtube_id,
        target_type: "youtube" as const,
        project_id: project.project_id,
        liked_disliked_id: undefined, // Will be set from likes data
        meta: {
          channel: "YouTube",
          duration: video.video_duration,
          views: video.video_views,
          likes: video.video_likes,
          video_url: video.video_url
        },
        feedback: undefined as "accept" | "reject" | undefined
      }));

      // Transform papers to Item format
      const paperItems: Item[] = completeData.papers.map((paper: any) => ({
        id: paper.paper_id,
        title: paper.paper_title,
        database_id: paper.paper_id,
        target_type: "paper" as const,
        project_id: project.project_id,
        liked_disliked_id: undefined, // Will be set from likes data
        meta: {
          venue: "ArXiv",
          year: paper.published_year,
          authors: paper.authors ? paper.authors.map((a: any) => a.name).join(', ') : 'Unknown',
          link: paper.pdf_link,
          pdf_link: paper.pdf_link,
          summary: paper.paper_summary
        },
        feedback: undefined as "accept" | "reject" | undefined
      }));

      // Apply likes to items - use the most recent like record for each item
      console.log('Applying likes from database:', completeData.likes);
      
      // Group likes by target (target_type + target_id) and keep only the most recent one
      const latestLikes = new Map();
      completeData.likes.forEach((like: any) => {
        const key = `${like.target_type}-${like.target_id}`;
        if (!latestLikes.has(key) || like.liked_disliked_id > latestLikes.get(key).liked_disliked_id) {
          latestLikes.set(key, like);
        }
      });
      
      // Apply the latest likes
      latestLikes.forEach((like: any) => {
        const items = like.target_type === 'youtube' ? youtubeItems : paperItems;
        const item = items.find(i => i.database_id === like.target_id);
        if (item) {
          console.log(`Applying like to item ${item.database_id}: isLiked=${like.isLiked}, liked_disliked_id=${like.liked_disliked_id}`);
          item.liked_disliked_id = like.liked_disliked_id;
          item.feedback = like.isLiked ? "accept" : "reject";
        } else {
          console.log(`No item found for like: target_type=${like.target_type}, target_id=${like.target_id}`);
        }
      });

      // Get the first query_id (most projects should have at least one query)
      const queryId = completeData.queries.length > 0 ? completeData.queries[0].query_id : 0;
      
      // Navigate to the next screen with complete data
      onProjectComplete(
        project.topic,
        project.objective,
        project.guidelines,
        youtubeItems,
        paperItems,
        project.project_id,
        queryId
      );
    } catch (error) {
      console.error('Failed to load project data:', error);
      setValidationError("Failed to load project data. Please try again.");
    }
  };

  const onRun = async () => {
    // Clear previous validation errors
    setValidationError("");
    
    // Check if user is logged in
    if (!user?.user_id) {
      setValidationError("Please sign in to generate content");
      return;
    }
    
    // Frontend validation
    if (!topic.trim()) {
      setValidationError("Topic is required");
      return;
    }
    if (!objective.trim()) {
      setValidationError("Objective is required");
      return;
    }
    if (!guidelines.trim()) {
      setValidationError("Guidelines are required");
      return;
    }

    setIsGenerating(true);
    console.log("Run button clicked!"); // Debug log
    console.log("Payload:", { topic, objective, guidelines, user_id: user.user_id }); // Debug log
    try { 
      console.log("Calling generateSubmission API...");
      const result = await generateSubmission(topic, objective, guidelines, user.user_id); 
      console.log("Submission generated:", result);
      console.log("YouTube array:", result.youtube);
      console.log("Papers array:", result.papers);
      console.log("Project ID:", result.project_id);
      
      // Debug: Check if database IDs are present
      if (result.youtube && result.youtube.length > 0) {
        console.log("First YouTube video from backend:", result.youtube[0]);
        console.log("YouTube video has youtube_id:", 'youtube_id' in result.youtube[0]);
        console.log("YouTube video keys:", Object.keys(result.youtube[0]));
      }
      if (result.papers && result.papers.length > 0) {
        console.log("First paper from backend:", result.papers[0]);
        console.log("Paper has paper_id:", 'paper_id' in result.papers[0]);
        console.log("Paper keys:", Object.keys(result.papers[0]));
      } 
      
      // Handle the new API response format
      if (result.success) {
        const projectId = result.project_id;
        const queryId = result.query_id;
        
        // Handle YouTube videos
        if (result.youtube && Array.isArray(result.youtube)) {
          const youtubeItems = result.youtube.map((video: any, index: number) => ({
            id: `youtube-${index}-${Date.now()}`,
            title: video.video_title,
            database_id: video.youtube_id, // Database ID for like/dislike
            target_type: "youtube" as const,
            project_id: projectId,
            meta: {
              channel: "YouTube", // We could extract channel from video data if needed
              duration: video.video_duration,
              views: video.video_views,
              likes: video.video_likes,
              video_url: video.video_url
            },
            feedback: undefined as "accept" | "reject" | undefined
          }));
          
          console.log("Created YouTube items with database info:", youtubeItems);
          if (youtubeItems.length > 0) {
            console.log("First YouTube item properties:", Object.keys(youtubeItems[0]));
            console.log("First YouTube item database_id:", youtubeItems[0].database_id);
            console.log("First YouTube item target_type:", youtubeItems[0].target_type);
            console.log("First YouTube item project_id:", youtubeItems[0].project_id);
          }
        }
        
        // Handle papers
        if (result.papers && Array.isArray(result.papers)) {
          const paperItems = result.papers.map((paper: any, index: number) => ({
            id: `paper-${index}-${Date.now()}`,
            title: paper.title,
            database_id: paper.paper_id, // Database ID for like/dislike
            target_type: "paper" as const,
            project_id: projectId,
            meta: {
              venue: "ArXiv", // ArXiv is the source
              year: new Date(paper.published).getFullYear(),
              authors: paper.authors ? paper.authors.join(', ') : 'Unknown',
              link: paper.link,
              pdf_link: paper.pdf_link,
              summary: paper.summary
            },
            feedback: undefined as "accept" | "reject" | undefined
          }));
          
          console.log("Created paper items with database info:", paperItems);
          if (paperItems.length > 0) {
            console.log("First paper item properties:", Object.keys(paperItems[0]));
            console.log("First paper item database_id:", paperItems[0].database_id);
            console.log("First paper item target_type:", paperItems[0].target_type);
            console.log("First paper item project_id:", paperItems[0].project_id);
          }
        }
        
        // Call the completion handler with the project details and generated items
        onProjectComplete(
          topic,
          objective,
          guidelines,
          result.youtube ? result.youtube.map((video: any, index: number) => ({
            id: `youtube-${index}-${Date.now()}`,
            title: video.video_title,
            database_id: video.youtube_id,
            target_type: "youtube" as const,
            project_id: projectId,
            meta: {
              channel: "YouTube",
              duration: video.video_duration,
              views: video.video_views,
              likes: video.video_likes,
              video_url: video.video_url
            },
            feedback: undefined as "accept" | "reject" | undefined
          })) : [],
          result.papers ? result.papers.map((paper: any, index: number) => ({
            id: `paper-${index}-${Date.now()}`,
            title: paper.title,
            database_id: paper.paper_id,
            target_type: "paper" as const,
            project_id: projectId,
            meta: {
              venue: "ArXiv",
              year: new Date(paper.published).getFullYear(),
              authors: paper.authors ? paper.authors.join(', ') : 'Unknown',
              link: paper.link,
              pdf_link: paper.pdf_link,
              summary: paper.summary
            },
            feedback: undefined as "accept" | "reject" | undefined
          })) : [],
          projectId,
          queryId
        );
      } else if (result.error) {
        setValidationError(result.error);
      }
    }
    catch (e) { 
      console.error("Error generating submission:", e);
      setValidationError("Failed to generate submission. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };


  return (
    <div className="min-h-screen flex flex-col bg-black text-white">
      {/* Sidebar - only show if user is logged in */}
      {user && (
        <ConversationsSidebar
          user={user}
          onProjectSelect={handleProjectSelect}
          isHovered={isSidebarHovered}
          onMouseEnter={() => setIsSidebarHovered(true)}
          onMouseLeave={() => setIsSidebarHovered(false)}
        />
      )}
      
      <HeaderBar />
      
      {/* Hoverable trigger section that replaces welcome section */}
      {user && (
        <div 
          className="w-full px-4 py-3 bg-zinc-900 border-b border-zinc-800 cursor-pointer hover:bg-zinc-800 transition-colors"
          onMouseEnter={() => setIsSidebarHovered(true)}
          onMouseLeave={() => setIsSidebarHovered(false)}
        >
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="text-sm text-zinc-400">Click or hover to view past conversations</span>
              <span className="text-sm text-pink-400">
                • Signed in as {user.name}
              </span>
            </div>
            <SimpleLogin 
              onLogin={onUserLogin}
              onLogout={onUserLogout}
              user={user}
            />
          </div>
        </div>
      )}
      
      {/* Show regular welcome section if not logged in */}
      {!user && (
        <div className="w-full px-4 py-3 bg-zinc-900 border-b border-zinc-800">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="text-sm text-zinc-400">Welcome to MemoScholar</span>
            </div>
            <SimpleLogin 
              onLogin={onUserLogin}
              onLogout={onUserLogout}
              user={user}
            />
          </div>
        </div>
      )}
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">

        <main className="flex-1 w-full px-8 py-12">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">Enter Your Project Details Below</h1>
            <p className="text-xl text-zinc-400">Provide the information needed to generate your research content</p>
          </div>

          <div className="space-y-8">
            {validationError && (
              <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
                <p className="text-red-400">{validationError}</p>
              </div>
            )}

            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-lg font-medium text-white">Topic</label>
                <Input 
                  value={topic} 
                  onChange={(e) => setTopic(e.target.value)} 
                  placeholder="e.g., Graph Neural Networks for Recommendation" 
                  className="text-lg py-4"
                />
              </div>

              <div className="space-y-3">
                <label className="text-lg font-medium text-white">Primary Objective</label>
                <Input 
                  value={objective} 
                  onChange={(e) => setObjective(e.target.value)} 
                  placeholder="e.g., build a GNN-based re-ranker" 
                  className="text-lg py-4"
                />
              </div>

              <div className="space-y-3">
                <label className="text-lg font-medium text-white">Guidelines</label>
                <Textarea 
                  value={guidelines} 
                  onChange={(e) => setGuidelines(e.target.value)} 
                  placeholder="e.g., submission guidelines, formatting requirements, specific instructions" 
                  className="text-lg py-4 min-h-[120px]"
                />
              </div>
            </div>

            <div className="flex justify-center pt-8">
              <Button 
                onClick={onRun} 
                variant="default" 
                disabled={isGenerating || !user?.user_id}
                size="lg"
                className={`px-12 py-4 text-lg ${isGenerating ? "bg-pink-500 hover:bg-pink-600" : ""}`}
              >
                <Play className={`h-6 w-6 mr-2 ${isGenerating ? 'animate-spin' : ''}`} /> 
                {isGenerating ? 'Generating...' : !user?.user_id ? 'Sign in to generate' : 'Generate Content'}
              </Button>
            </div>
          </div>
        </div>
        </main>
      </div>
    </div>
  );
}
