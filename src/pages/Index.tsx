import Hero from "@/components/portfolio/Hero";
import Projects from "@/components/portfolio/Projects";
import Experience from "@/components/portfolio/Experience";
import Links from "@/components/portfolio/Links";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Hero />
      <Projects />
      <Experience />
      <Links />
    </div>
  );
};

export default Index;
