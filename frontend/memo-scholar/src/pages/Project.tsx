import { useState } from "react";
import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { HeaderBar } from "@/components/ui/header_bar";
import { generateSubmission } from "@/lib/api";
import type { Item } from "@/types";

interface ProjectProps {
  onProjectComplete: (topic: string, objective: string, guidelines: string, youtubeItems: Item[], paperItems: Item[]) => void;
}

export default function Project({ onProjectComplete }: ProjectProps) {
  const [topic, setTopic] = useState("");
  const [objective, setObjective] = useState("");
  const [guidelines, setGuidelines] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [validationError, setValidationError] = useState<string>("");

  const onRun = async () => {
    // Clear previous validation errors
    setValidationError("");
    
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
    console.log("Payload:", { topic, objective, guidelines }); // Debug log
    try { 
      console.log("Calling generateSubmission API...");
      const result = await generateSubmission(topic, objective, guidelines); 
      console.log("Submission generated:", result);
      console.log("YouTube array:", result.youtube);
      console.log("Papers array:", result.papers); 
      
      // Handle the new API response format
      if (result.success) {
        // Handle YouTube videos
        if (result.youtube && Array.isArray(result.youtube)) {
          const youtubeItems = result.youtube.map((video: any, index: number) => ({
            id: `youtube-${index}-${Date.now()}`,
            title: video.video_title,
            meta: {
              channel: "YouTube", // We could extract channel from video data if needed
              duration: video.video_duration,
              views: video.video_views,
              likes: video.video_likes,
              video_url: video.video_url
            },
            feedback: undefined as "accept" | "reject" | undefined
          }));
          
          console.log("Created YouTube items:", youtubeItems);
        }
        
        // Handle papers
        if (result.papers && Array.isArray(result.papers)) {
          const paperItems = result.papers.map((paper: any, index: number) => ({
            id: `paper-${index}-${Date.now()}`,
            title: paper.title,
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
          
          console.log("Created paper items:", paperItems);
        }
        
        // Call the completion handler with the project details and generated items
        onProjectComplete(
          topic,
          objective,
          guidelines,
          result.youtube ? result.youtube.map((video: any, index: number) => ({
            id: `youtube-${index}-${Date.now()}`,
            title: video.video_title,
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
            meta: {
              venue: "ArXiv",
              year: new Date(paper.published).getFullYear(),
              authors: paper.authors ? paper.authors.join(', ') : 'Unknown',
              link: paper.link,
              pdf_link: paper.pdf_link,
              summary: paper.summary
            },
            feedback: undefined as "accept" | "reject" | undefined
          })) : []
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
      <HeaderBar />

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
                disabled={isGenerating}
                size="lg"
                className={`px-12 py-4 text-lg ${isGenerating ? "bg-pink-500 hover:bg-pink-600" : ""}`}
              >
                <Play className={`h-6 w-6 mr-2 ${isGenerating ? 'animate-spin' : ''}`} /> 
                {isGenerating ? 'Generating...' : 'Generate Content'}
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
