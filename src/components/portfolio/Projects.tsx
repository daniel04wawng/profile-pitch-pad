import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const Projects = () => {
  const projects = [
    {
      title: "Project Title 1",
      subtitle: "Brief Description",
      status: "LIVE • YEAR",
      gradient: "var(--gradient-orange-purple)",
      description: "Add your project description here. Explain what it does, technologies used, and your role."
    },
    {
      title: "Project Title 2", 
      subtitle: "Brief Description",
      status: "SHIPPED • YEAR",
      gradient: "var(--gradient-blue-purple)",
      description: "Add your project description here. Explain what it does, technologies used, and your role."
    },
    {
      title: "Project Title 3",
      subtitle: "Brief Description", 
      status: "IN PROGRESS • YEAR",
      gradient: "var(--gradient-pink-orange)",
      description: "Add your project description here. Explain what it does, technologies used, and your role."
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-light mb-16">Cool Projects I've Built</h2>
        
        <div className="grid md:grid-cols-2 gap-8">
          {projects.map((project, index) => (
            <Card key={index} className="group cursor-pointer hover:shadow-lg transition-all duration-300 border-0 overflow-hidden">
              <div 
                className="h-48 flex items-center justify-center text-white font-light text-2xl"
                style={{ background: project.gradient }}
              >
                {project.title}
              </div>
              <CardContent className="p-6">
                <div className="mb-4">
                  <h3 className="text-xl font-medium mb-2">{project.title}</h3>
                  <Badge variant="outline" className="text-xs">
                    {project.status}
                  </Badge>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  {project.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Projects;