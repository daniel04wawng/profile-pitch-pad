import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Calendar, MapPin } from "lucide-react";

const Experience = () => {
  const hackathons = [
    {
      title: "Hackathon Name 1",
      award: "1st Place",
      date: "2024",
      location: "Location",
      project: "Project Name",
      description: "Brief description of what you built and achieved"
    },
    {
      title: "Hackathon Name 2", 
      award: "Best Design",
      date: "2024",
      location: "Location",
      project: "Project Name",
      description: "Brief description of what you built and achieved"
    },
    {
      title: "Hackathon Name 3",
      award: "People's Choice",
      date: "2023", 
      location: "Location",
      project: "Project Name",
      description: "Brief description of what you built and achieved"
    }
  ];

  const experiences = [
    {
      role: "Job Title",
      company: "Company Name",
      period: "Start Date - End Date",
      location: "Location",
      description: "Brief description of your role and key achievements"
    },
    {
      role: "Job Title",
      company: "Company Name", 
      period: "Start Date - End Date",
      location: "Location",
      description: "Brief description of your role and key achievements"
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24 bg-secondary/30">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-light mb-16">Experience & Achievements</h2>
        
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Hackathons & Wins */}
          <div>
            <h3 className="text-2xl font-medium mb-8 flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              Hackathon Wins
            </h3>
            <div className="space-y-6">
              {hackathons.map((hackathon, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg">{hackathon.title}</CardTitle>
                      <Badge variant="secondary">{hackathon.award}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {hackathon.date}
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {hackathon.location}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="font-medium mb-2">{hackathon.project}</p>
                    <p className="text-muted-foreground text-sm">{hackathon.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Work Experience */}
          <div>
            <h3 className="text-2xl font-medium mb-8">Work Experience</h3>
            <div className="space-y-6">
              {experiences.map((exp, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">{exp.role}</CardTitle>
                    <div className="flex justify-between items-center text-sm text-muted-foreground">
                      <span className="font-medium">{exp.company}</span>
                      <span>{exp.period}</span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <MapPin className="w-4 h-4" />
                      {exp.location}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground text-sm">{exp.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Experience;