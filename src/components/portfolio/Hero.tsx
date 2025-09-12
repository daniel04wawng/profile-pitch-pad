import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Download, Github, Linkedin, Mail } from "lucide-react";

const Hero = () => {
  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-4xl mx-auto text-center">
        <div className="mb-8">
          <h1 className="text-4xl md:text-6xl font-light mb-6">
            Hi, I'm <span className="font-medium">Daniel Wang</span>
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground mb-8">
            Full-Stack Developer & Problem Solver
          </p>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-12">
            I build innovative solutions that bridge the gap between ideas and reality. 
            Passionate about creating meaningful technology that makes a difference.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <Button size="lg" asChild>
            <a href="mailto:daniel04wang@gmail.com">
              <Mail className="w-5 h-5 mr-2" />
              Get In Touch
            </a>
          </Button>
          <Button variant="outline" size="lg" asChild>
            <a href="https://github.com/daniel04wawng" target="_blank" rel="noopener noreferrer">
              <Github className="w-5 h-5 mr-2" />
              View My Work
            </a>
          </Button>
        </div>

        <Card className="max-w-2xl mx-auto">
          <CardContent className="p-8">
            <h3 className="text-xl font-medium mb-4">Quick Pitch</h3>
            <p className="text-muted-foreground leading-relaxed">
              I'm a dedicated developer with a passion for building solutions that matter. 
              Whether it's a hackathon project that solves real-world problems or a 
              full-stack application that streamlines workflows, I bring creativity, 
              technical expertise, and a user-focused approach to every project.
            </p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};

export default Hero;
