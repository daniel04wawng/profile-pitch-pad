import { Badge } from "@/components/ui/badge";
import { motion, useScroll, useTransform, useInView } from "framer-motion";
import { useRef } from "react";

const Hero = () => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: false, amount: 0.3 });
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 300], [0, -50]);
  const opacity = useTransform(scrollY, [0, 300], [1, 0.7]);

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-6xl mx-auto">
        <motion.div 
          ref={ref}
          className="grid md:grid-cols-2 gap-24 items-center"
          style={{ y, opacity }}
        >
          {/* Text Content */}
          <motion.div 
            className="text-center md:text-left"
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            
            <div className="mb-8">
              <h1 className="text-5xl md:text-6xl lg:text-7xl font-light leading-tight mb-6">
                I'm <span className="font-medium">Daniel Wang</span> and I bring ideas to life with{" "}
                <span className="italic font-light">collaboration + impact</span>.
              </h1>
              
              <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed">
                I just finished my third year at Ivey Business School in Canada, and I'm now on leave to solve some of the largest problems in the world. I am passionate about creating unforgettable expereinces through technology + community
              </p>
            </div>
            <div className="mb-8">
              <Badge variant="secondary" className="mb-4">
                NOW
              </Badge>
              <div className="grid md:grid-cols-2 gap-8 text-sm text-muted-foreground mb-8">
                <div>
                  <p className="font-medium text-foreground">Current Role</p>
                  <p>Product Management Intern</p>
                </div>
                <div>
                  <p className="font-medium text-foreground">Current Focus</p>
                  <p>NimbleRx</p>
                </div>
              </div>
            </div>
            <div className="mb-8">
              <Badge variant="secondary" className="mb-4">
                PREVIOUSLY
              </Badge>
              <div className="grid md:grid-cols-2 gap-8 text-sm text-muted-foreground">
                <div className="space-y-2">
                  <p>KPMG</p>
                  <p>Vitalis</p>
                </div>
                <div className="space-y-2">
                  <p>Consulting Intern</p>
                  <p>ESG Analyst Intern</p>
                </div>
              </div>
            </div>


          </motion.div>
          
          {/* Profile Picture */}
          <motion.div 
            className="flex justify-center md:justify-end"
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
            transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
          >
            <div className="relative">
              <img 
                src="/IMG_1935.jpeg" 
                alt="Daniel Wang" 
                className="w-80 h-80 rounded-full object-cover shadow-2xl"
              />
              {/* Little bubbles */}
              <div className="absolute -top-4 -left-4 w-6 h-6 bg-blue-500 rounded-full opacity-80 animate-pulse"></div>
              <div className="absolute -bottom-2 -left-8 w-4 h-4 bg-purple-500 rounded-full opacity-60 animate-pulse delay-1000"></div>
              <div className="absolute top-1/2 -right-6 w-5 h-5 bg-green-500 rounded-full opacity-70 animate-pulse delay-500"></div>
              <div className="absolute -top-8 right-4 w-3 h-3 bg-pink-500 rounded-full opacity-50 animate-pulse delay-700"></div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
