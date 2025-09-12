import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ExternalLink, Github, Linkedin, Mail, FileText } from "lucide-react";

const Links = () => {
  const links = [
    {
      name: "Devpost",
      url: "https://devpost.com/daniel04wang",
      icon: <ExternalLink className="w-5 h-5" />,
      description: "Check out my hackathon projects"
    },
    {
      name: "GitHub", 
      url: "https://github.com/daniel04wawng",
      icon: <Github className="w-5 h-5" />,
      description: "View my code repositories"
    },
    {
      name: "LinkedIn",
      url: "https://www.linkedin.com/in/daniel04wang/", 
      icon: <Linkedin className="w-5 h-5" />,
      description: "Connect with me professionally"
    },
    {
      name: "Email",
      url: "mailto:daniel04wang@gmail.com",
      icon: <Mail className="w-5 h-5" />,
      description: "Get in touch directly"
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-light mb-6">Let's Connect</h2>
        <p className="text-muted-foreground text-lg mb-16 max-w-2xl mx-auto">
          Interested in collaborating or just want to chat? Here's where you can find me online.
        </p>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {links.map((link, index) => (
            <Card key={index} className="group hover:shadow-lg transition-all duration-300 cursor-pointer">
              <CardContent className="p-6 text-center">
                <div className="mb-4 flex justify-center">
                  <div className="p-3 rounded-full bg-primary/10 group-hover:bg-primary/20 transition-colors">
                    {link.icon}
                  </div>
                </div>
                <h3 className="font-medium mb-2">{link.name}</h3>
                <p className="text-sm text-muted-foreground mb-4">{link.description}</p>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                  asChild
                >
                  <a href={link.url} target="_blank" rel="noopener noreferrer">
                    Visit
                  </a>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <p className="text-muted-foreground mb-6">
            Want to work together on something cool?
          </p>
          <Button size="lg" asChild>
            <a href="mailto:daniel04wang@gmail.com">
              <Mail className="w-5 h-5 mr-2" />
              Let's Talk
            </a>
          </Button>
        </div>
      </div>
    </section>
  );
};

export default Links;