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
              <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
                <div className="grid grid-cols-4 h-[80vh]">
                  {/* Sidebar Navigation */}
                  <div className="col-span-1 border-r bg-muted/30 p-6 overflow-y-auto">
                    <div className="mb-8">
                      <h2 className="text-lg font-semibold mb-2">{project.title}</h2>
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <div><strong>Role:</strong> Product Developer</div>
                        <div><strong>Timeline:</strong> {project.status.split(' • ')[1] || '2024'}</div>
                        <div><strong>Team:</strong> {project.company}</div>
                        <div><strong>Skills:</strong> AI/ML, Product Strategy, Full-Stack Development</div>
                      </div>
                    </div>
                    <Tabs defaultValue="overview" orientation="vertical" className="w-full">
                      <TabsList className="flex flex-col h-auto w-full bg-transparent p-0 space-y-1">
                        <TabsTrigger value="overview" className="w-full justify-start data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                          Overview
                        </TabsTrigger>
                        <TabsTrigger value="problem" className="w-full justify-start data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                          Into the Problem Space
                        </TabsTrigger>
                        <TabsTrigger value="research" className="w-full justify-start data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                          Research & Analysis
                        </TabsTrigger>
                        <TabsTrigger value="solution" className="w-full justify-start data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                          Solution
                        </TabsTrigger>
                        <TabsTrigger value="outcome" className="w-full justify-start data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
                          Impact & Reflection
                        </TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                  
                  {/* Main Content Area */}
                  <div className="col-span-3 p-8 overflow-y-auto">
                    <Tabs defaultValue="overview" orientation="vertical">
                      <TabsContent value="overview" className="mt-0">
                        <div className="space-y-6">
                          <h3 className="text-2xl font-bold mb-4">Overview</h3>
                          <div 
                            className="h-48 rounded-lg flex items-center justify-center text-white font-light text-xl mb-6"
                            style={{ background: project.gradient }}
                          >
                            {project.subtitle}
                          </div>
                          <p className="text-lg leading-relaxed">{project.details.what}</p>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="problem" className="mt-0">
                        <div className="space-y-6">
                          <h3 className="text-2xl font-bold">The Problem</h3>
                          <p className="text-lg leading-relaxed">{project.details.problem}</p>
                          <div className="bg-muted p-6 rounded-lg">
                            <h4 className="font-semibold mb-2">Challenge Statement</h4>
                            <p className="text-muted-foreground">How might we address the core issues identified in this space while creating meaningful value for users?</p>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="research" className="mt-0">
                        <div className="space-y-6">
                          <h3 className="text-2xl font-bold">Research & Development Process</h3>
                          <p className="text-lg leading-relaxed">{project.details.process}</p>
                          <div className="grid gap-4">
                            <div className="bg-muted p-4 rounded-lg">
                              <h4 className="font-semibold mb-2">Key Technologies</h4>
                              <p className="text-sm text-muted-foreground">AI/ML algorithms, data processing pipelines, user interface design</p>
                            </div>
                            <div className="bg-muted p-4 rounded-lg">
                              <h4 className="font-semibold mb-2">Development Approach</h4>
                              <p className="text-sm text-muted-foreground">Iterative development with continuous user feedback and testing</p>
                            </div>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="solution" className="mt-0">
                        <div className="space-y-6">
                          <h3 className="text-2xl font-bold">Solution</h3>
                          <p className="text-lg leading-relaxed">{project.details.solution}</p>
                          <div className="bg-primary/10 p-6 rounded-lg border-l-4 border-primary">
                            <h4 className="font-semibold mb-2">Core Innovation</h4>
                            <p>This solution leverages cutting-edge technology to create a seamless user experience while addressing the fundamental challenges in the problem space.</p>
                          </div>
                        </div>
                      </TabsContent>
                      
                      <TabsContent value="outcome" className="mt-0">
                        <div className="space-y-6">
                          <h3 className="text-2xl font-bold">Impact & Results</h3>
                          <p className="text-lg leading-relaxed">{project.details.outcome}</p>
                          <div className="grid md:grid-cols-2 gap-4">
                            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                              <h4 className="font-semibold text-green-800 mb-2">Key Metrics</h4>
                              <p className="text-sm text-green-700">Significant improvements in efficiency and user satisfaction</p>
                            </div>
                            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                              <h4 className="font-semibold text-blue-800 mb-2">Lessons Learned</h4>
                              <p className="text-sm text-blue-700">Valuable insights gained from user feedback and iterative development</p>
                            </div>
                          </div>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Projects;