import { Badge } from "@/components/ui/badge";

const Hero = () => {
  return (
    <section className="min-h-screen flex items-center px-6 md:px-12 lg:px-24">
      <div className="max-w-4xl">
        <div className="mb-8">
          <Badge variant="secondary" className="mb-4">
            NOW
          </Badge>
          <div className="grid md:grid-cols-2 gap-8 text-sm text-muted-foreground mb-8">
            <div>
              <p className="font-medium text-foreground">Current Role</p>
              <p>Add your current position here</p>
            </div>
            <div>
              <p className="font-medium text-foreground">Current Focus</p>
              <p>Add your current focus area here</p>
            </div>
          </div>
        </div>
        
        <div className="mb-8">
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-light leading-tight mb-6">
            I'm <span className="font-medium">[Your Name]</span> and I bring ideas to life with{" "}
            <span className="italic font-light">design + code</span>.
          </h1>
          
          <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed">
            [Add your intro text here - describe what you do, your passion, and what you're currently working on or thinking about]
          </p>
        </div>

        <div className="mb-8">
          <Badge variant="secondary" className="mb-4">
            PREVIOUSLY
          </Badge>
          <div className="grid md:grid-cols-2 gap-8 text-sm text-muted-foreground">
            <div className="space-y-2">
              <p>[Previous Company 1]</p>
              <p>[Previous Company 2]</p>
              <p>[Previous Company 3]</p>
              <p>[Previous Company 4]</p>
            </div>
            <div className="space-y-2">
              <p>[Previous Role 1]</p>
              <p>[Previous Role 2]</p>
              <p>[Previous Role 3]</p>
              <p>[Previous Role 4]</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;