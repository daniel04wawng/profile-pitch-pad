import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Calendar, MapPin } from "lucide-react";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const Experience = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: false, amount: 0.2 });

  const achievements = [
    {
      title: "Cal Hacks 11.0",
      award: "First Place Grand Prize",
      date: "Oct 2024",
      location: "UC Berkeley",
      description: "Built the world's first brain-computer interface that converts neural activity directly into musical compositions using EEG sensors and ML algorithms"
    },
    {
      title: "Hack Western 10.0", 
      award: "Best Hardware Hack",
      date: "Nov 2024",
      location: "Western University",
      description: "Created an AR application that visualizes solar panel installations on buildings with 90% accuracy in placement recommendations"
    },
    {
      title: "McKinsey Case Competition",
      award: "1st out of 1000 competitors",
      date: "2024", 
      location: "Western University",
      description: "Competed in McKinsey's case competition, developing strategic solutions for complex business challenges and presenting to senior consultants"
    },
    
  ];

  const experiences = [
    {
      role: "Product Management Intern",
      company: "NimbleRx",
      period: "Summer 2025",
      location: "San Francisco, CA",
      description: "Led product initiatives for AI-powered healthcare solutions including Mira AI digital patient twin"                                                                                                 
    },
    {
      role: "Consulting Intern",
      company: "KPMG", 
      period: "Summer 2024",
      location: "Vancouver, BC",
      description: "Developed automated compliance solutions and consulted on regulatory technology implementations"                                                                                                    
    },
    {
      role: "ESG Analyst Intern",
      company: "Vitalis",
      period: "2024",
      location: "Remote",
      description: "Analyzed environmental, social, and governance factors for sustainable investment decisions"                                                                                                        
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-6xl mx-auto">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <h2 className="text-3xl md:text-4xl font-light mb-16">Experience & Achievements</h2>
        </motion.div>
        
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Achievements & Competitions */}
          <div>
            <h3 className="text-2xl font-medium mb-8 flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              Achievements & Competitions
            </h3>
            <div className="space-y-6">
              {achievements.map((achievement, index) => {
                const cardRef = useRef(null);
                const cardInView = useInView(cardRef, { once: true, amount: 0.2 });
                
                return (
                  <motion.div
                    key={index}
                    ref={cardRef}
                    initial={{ opacity: 0, y: 30 }}
                    animate={cardInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
                    transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
                  >
                    <Card className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg">{achievement.title}</CardTitle>
                      <Badge variant="outline" className="bg-muted/50 text-foreground">{achievement.award}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {achievement.date}
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {achievement.location}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="font-medium mb-2">{achievement.project}</p>
                    <p className="text-muted-foreground text-sm">{achievement.description}</p>
                  </CardContent>
                </Card>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Work Experience */}
          <div>
            <h3 className="text-2xl font-medium mb-8">Work Experience</h3>
            <div className="space-y-6">
              {experiences.map((exp, index) => {
                const cardRef = useRef(null);
                const cardInView = useInView(cardRef, { once: true, amount: 0.2 });
                
                return (
                  <motion.div
                    key={index}
                    ref={cardRef}
                    initial={{ opacity: 0, y: 30 }}
                    animate={cardInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
                    transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
                  >
                    <Card className="hover:shadow-md transition-shadow">
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
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Experience;