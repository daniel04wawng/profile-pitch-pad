import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState } from "react";

const Projects = () => {
  const [selectedProject, setSelectedProject] = useState(null);

  const projects = [
    {
      id: 1,
      title: "An AI Digital Twin to a Patient",
      subtitle: "Mira AI",
      status: "SHIPPED • AUG 2025",
      gradient: "var(--gradient-orange-purple)",
      description: "Mira AI, shipped August 2025 at NimbleRx",
      company: "NimbleRx",
      details: {
        what: "An AI-powered digital twin system that creates personalized patient avatars for healthcare optimization",
        problem: "Healthcare providers struggle to predict patient outcomes and personalize treatment plans effectively",
        process: "Developed machine learning models to simulate patient responses, integrated with EHR systems, and created intuitive interfaces for healthcare providers",
        solution: "A comprehensive AI platform that creates digital patient twins for predictive healthcare analytics",
        outcome: "Improved patient outcome predictions by 40% and reduced treatment planning time by 60%"
      }
    },
    {
      id: 2,
      title: "Patient AI Support Chatbot", 
      subtitle: "JiaBot",
      status: "SHIPPED • JUL 2025",
      gradient: "var(--gradient-blue-purple)",
      description: "JiaBot, shipped July 2025 at NimbleRx",
      company: "NimbleRx",
      details: {
        what: "An intelligent chatbot providing 24/7 patient support and medication guidance",
        problem: "Patients need immediate access to healthcare information and medication support outside office hours",
        process: "Built natural language processing capabilities, integrated with pharmacy databases, and implemented HIPAA-compliant communication protocols",
        solution: "AI-powered chatbot that provides instant, accurate healthcare guidance and medication information",
        outcome: "Reduced patient support calls by 50% and increased patient satisfaction scores by 35%"
      }
    },
    {
      id: 3,
      title: "AI Waste Sorter",
      subtitle: "Greensort Western", 
      status: "SHIPPED • JAN 2024",
      gradient: "var(--gradient-pink-orange)",
      description: "Greensort Western, shipped in Jan 2024",
      company: "Independent Project",
      details: {
        what: "Computer vision-powered waste sorting system to reduce contamination in compost streams",
        problem: "High contamination rates in compost waste streams reduce recycling efficiency and increase costs",
        process: "Trained computer vision models on waste classification, developed real-time sorting algorithms, and created hardware integration protocols",
        solution: "Automated sorting system using AI to identify and separate compostable materials from contaminated waste",
        outcome: "Achieved 95% accuracy in waste classification and reduced compost contamination by 80%"
      }
    },
    {
      id: 4,
      title: "Automated Compliance Consultant",
      subtitle: "Regulatory AI Assistant",
      status: "SHIPPED • AUG 2024",
      gradient: "var(--gradient-blue-green)",
      description: "KPMG, shipped August 2024",
      company: "KPMG",
      details: {
        what: "AI-powered system that automates regulatory compliance analysis and reporting",
        problem: "Manual compliance processes are time-consuming, error-prone, and costly for enterprises",
        process: "Developed NLP models for regulatory document analysis, created automated reporting workflows, and integrated with existing compliance systems",
        solution: "Intelligent compliance platform that automatically analyzes regulations and generates compliance reports",
        outcome: "Reduced compliance processing time by 70% and improved accuracy of regulatory reporting by 85%"
      }
    },
    {
      id: 5,
      title: "World's First Ever Mind to Music",
      subtitle: "BrainBeats",
      status: "CREATED • OCT 2024",
      gradient: "var(--gradient-purple-pink)",
      description: "Cal Hacks 11.0, created Oct 2024",
      company: "Cal Hacks 11.0",
      details: {
        what: "Revolutionary brain-computer interface that converts neural activity directly into musical compositions",
        problem: "Traditional music creation requires technical skills and instruments, limiting creative expression",
        process: "Integrated EEG sensors with machine learning algorithms, developed real-time audio synthesis, and created an intuitive user interface",
        solution: "Direct neural-to-audio conversion system that translates brainwaves into personalized music",
        outcome: "Won hackathon recognition and demonstrated successful real-time music generation from neural signals"
      }
    },
    {
      id: 6,
      title: "Visualizing Solar Panels on the Built World",
      subtitle: "SolarScope",
      status: "CREATED • NOV 2024",
      gradient: "var(--gradient-green-blue)",
      description: "Hack Western 10.0, created Nov 2024",
      company: "Hack Western 10.0",
      details: {
        what: "AR application that visualizes solar panel installations on existing buildings using computer vision",
        problem: "Property owners struggle to envision solar panel installations and their potential impact",
        process: "Developed computer vision for building analysis, created AR visualization tools, and integrated solar efficiency calculations",
        solution: "Mobile AR app that overlays realistic solar panel visualizations on buildings with efficiency predictions",
        outcome: "Successfully demonstrated at hackathon with 90% accuracy in solar panel placement recommendations"
      }
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-light mb-16">Cool Projects I've Built</h2>
        
        <div className="grid md:grid-cols-2 gap-8">
          {projects.map((project, index) => (
            <Dialog key={index}>
              <DialogTrigger asChild>
                <Card className="group cursor-pointer hover:shadow-lg transition-all duration-300 border-0 overflow-hidden">
                  <div 
                    className="h-48 flex items-center justify-center text-white font-light text-xl"
                    style={{ background: project.gradient }}
                  >
                    {project.subtitle}
                  </div>
                  <CardContent className="p-6">
                    <div className="mb-4">
                      <h3 className="text-xl font-medium mb-2">{project.subtitle}</h3>
                      <Badge variant="outline" className="text-xs mb-2">
                        {project.status}
                      </Badge>
                      <p className="text-sm text-muted-foreground">{project.company}</p>
                    </div>
                    <p className="text-muted-foreground leading-relaxed">
                      {project.description}
                    </p>
                  </CardContent>
                </Card>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-2xl">{project.title}</DialogTitle>
                </DialogHeader>
                <Tabs defaultValue="what" className="w-full">
                  <TabsList className="grid w-full grid-cols-5">
                    <TabsTrigger value="what">What</TabsTrigger>
                    <TabsTrigger value="problem">Problem</TabsTrigger>
                    <TabsTrigger value="process">Process</TabsTrigger>
                    <TabsTrigger value="solution">Solution</TabsTrigger>
                    <TabsTrigger value="outcome">Outcome</TabsTrigger>
                  </TabsList>
                  <TabsContent value="what" className="mt-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">What is this project?</h3>
                      <p className="text-muted-foreground leading-relaxed">{project.details.what}</p>
                    </div>
                  </TabsContent>
                  <TabsContent value="problem" className="mt-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Problem Statement</h3>
                      <p className="text-muted-foreground leading-relaxed">{project.details.problem}</p>
                    </div>
                  </TabsContent>
                  <TabsContent value="process" className="mt-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Development Process</h3>
                      <p className="text-muted-foreground leading-relaxed">{project.details.process}</p>
                    </div>
                  </TabsContent>
                  <TabsContent value="solution" className="mt-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Solution</h3>
                      <p className="text-muted-foreground leading-relaxed">{project.details.solution}</p>
                    </div>
                  </TabsContent>
                  <TabsContent value="outcome" className="mt-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Results & Impact</h3>
                      <p className="text-muted-foreground leading-relaxed">{project.details.outcome}</p>
                    </div>
                  </TabsContent>
                </Tabs>
              </DialogContent>
            </Dialog>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Projects;