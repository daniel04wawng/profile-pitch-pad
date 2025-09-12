import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Github } from "lucide-react";

const Projects = () => {
  const projects = [
    {
      title: "AI-Powered Learning Platform",
      description: "A comprehensive educational platform that uses machine learning to personalize learning experiences and track student progress.",
      technologies: ["React", "Node.js", "Python", "TensorFlow", "MongoDB"],
      github: "https://github.com/daniel04wawng/ai-learning-platform",
      demo: "https://ai-learning-demo.vercel.app",
      featured: true
    },
    {
      title: "Smart City Dashboard",
      description: "Real-time dashboard for monitoring city infrastructure, traffic patterns, and environmental data with interactive visualizations.",
      technologies: ["Next.js", "TypeScript", "D3.js", "PostgreSQL", "Docker"],
      github: "https://github.com/daniel04wawng/smart-city-dashboard",
      demo: "https://smart-city-demo.vercel.app",
      featured: true
    },
    {
      title: "E-commerce Analytics Tool",
      description: "Advanced analytics platform for e-commerce businesses with predictive insights and customer behavior analysis.",
      technologies: ["Vue.js", "Python", "FastAPI", "Redis", "AWS"],
      github: "https://github.com/daniel04wawng/ecommerce-analytics",
      demo: "https://ecommerce-analytics.vercel.app",
      featured: false
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24 bg-muted/30">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-light mb-6">Featured Projects</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Here are some of the projects I'm most proud of. Each one represents 
            a unique challenge and an opportunity to create something meaningful.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {projects.map((project, index) => (
            <Card key={index} className={`group hover:shadow-lg transition-all duration-300 ${project.featured ? 'md:col-span-2 lg:col-span-1' : ''}`}>
              <CardHeader>
                <div className="flex items-start justify-between mb-2">
                  <CardTitle className="text-xl">{project.title}</CardTitle>
                  {project.featured && (
                    <Badge variant="secondary">Featured</Badge>
                  )}
                </div>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {project.description}
                </p>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2 mb-6">
                  {project.technologies.map((tech, techIndex) => (
                    <Badge key={techIndex} variant="outline" className="text-xs">
                      {tech}
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" asChild>
                    <a href={project.github} target="_blank" rel="noopener noreferrer">
                      <Github className="w-4 h-4 mr-2" />
                      Code
                    </a>
                  </Button>
                  <Button size="sm" asChild>
                    <a href={project.demo} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Demo
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="text-center mt-12">
          <Button variant="outline" size="lg" asChild>
            <a href="https://github.com/daniel04wawng" target="_blank" rel="noopener noreferrer">
              <Github className="w-5 h-5 mr-2" />
              View All Projects on GitHub
            </a>
          </Button>
        </div>
      </div>
    </section>
  );
};

export default Projects;
