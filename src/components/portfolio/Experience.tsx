import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, MapPin, Building2 } from "lucide-react";

const Experience = () => {
  const experiences = [
    {
      title: "Full-Stack Developer",
      company: "Tech Innovation Lab",
      location: "San Francisco, CA",
      period: "2023 - Present",
      description: "Leading development of scalable web applications and mentoring junior developers. Implemented microservices architecture that improved system performance by 40%.",
      technologies: ["React", "Node.js", "AWS", "Docker", "PostgreSQL"],
      type: "Full-time"
    },
    {
      title: "Frontend Developer Intern",
      company: "StartupXYZ",
      location: "Remote",
      period: "2022 - 2023",
      description: "Developed responsive user interfaces and collaborated with design team to create intuitive user experiences. Contributed to a 50% increase in user engagement.",
      technologies: ["Vue.js", "TypeScript", "Tailwind CSS", "Figma"],
      type: "Internship"
    },
    {
      title: "Freelance Web Developer",
      company: "Various Clients",
      location: "Remote",
      period: "2021 - 2022",
      description: "Built custom websites and web applications for small businesses. Specialized in e-commerce solutions and content management systems.",
      technologies: ["WordPress", "PHP", "JavaScript", "MySQL"],
      type: "Freelance"
    }
  ];

  const education = [
    {
      degree: "Bachelor of Science in Computer Science",
      school: "University of California, Berkeley",
      year: "2020 - 2024",
      description: "Focused on software engineering, algorithms, and data structures. Graduated Magna Cum Laude."
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-light mb-6">Experience & Education</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            My journey in technology has been driven by curiosity and a desire to 
            solve complex problems through innovative solutions.
          </p>
        </div>

        <div className="space-y-12">
          {/* Experience */}
          <div>
            <h3 className="text-2xl font-medium mb-8 text-center">Professional Experience</h3>
            <div className="space-y-6">
              {experiences.map((exp, index) => (
                <Card key={index} className="group hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-4">
                      <div>
                        <CardTitle className="text-xl mb-2">{exp.title}</CardTitle>
                        <div className="flex items-center text-muted-foreground mb-2">
                          <Building2 className="w-4 h-4 mr-2" />
                          <span className="font-medium">{exp.company}</span>
                        </div>
                        <div className="flex items-center text-muted-foreground mb-2">
                          <MapPin className="w-4 h-4 mr-2" />
                          <span>{exp.location}</span>
                        </div>
                        <div className="flex items-center text-muted-foreground">
                          <Calendar className="w-4 h-4 mr-2" />
                          <span>{exp.period}</span>
                        </div>
                      </div>
                      <Badge variant="secondary" className="mt-2 md:mt-0">
                        {exp.type}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-4 leading-relaxed">
                      {exp.description}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {exp.technologies.map((tech, techIndex) => (
                        <Badge key={techIndex} variant="outline" className="text-xs">
                          {tech}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Education */}
          <div>
            <h3 className="text-2xl font-medium mb-8 text-center">Education</h3>
            <div className="space-y-6">
              {education.map((edu, index) => (
                <Card key={index} className="group hover:shadow-lg transition-all duration-300">
                  <CardHeader>
                    <CardTitle className="text-xl mb-2">{edu.degree}</CardTitle>
                    <div className="flex items-center text-muted-foreground mb-2">
                      <Building2 className="w-4 h-4 mr-2" />
                      <span className="font-medium">{edu.school}</span>
                    </div>
                    <div className="flex items-center text-muted-foreground">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span>{edu.year}</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">
                      {edu.description}
                    </p>
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
