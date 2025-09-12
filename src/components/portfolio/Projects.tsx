move import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useRef } from "react";
import { motion, useScroll, useTransform, useInView } from "framer-motion";

const Projects = () => {
  const [selectedProject, setSelectedProject] = useState(null);

  const projects = [
    {
      id: 1,
      title: "Building a Healthcare Assistant Patients Can Trust",
      subtitle: "Mira AI",
      status: "SHIPPED • Aug 2025",
      gradient: "var(--gradient-orange-purple)",
      description: "Mira AI, shipped August 2025",
      company: "NimbleRx",
      role: "Product Manager",
      timeline: "Aug 2025",
      team: "NimbleRx",
      skills: "AI/ML, Product Strategy, Healthcare Tech",
      details: {
          intro: "Most healthcare chatbots cannot recall previous conversations or personalize answers in a meaningful way. Mira AI set out to change that by:\n\n• Storing and recalling relevant patient context\n• Delivering more accurate and empathetic answers using that context\n• Evaluating these features in a safe, testable environment\n\nAnother challenge was retention. Many patients only opened the app to order medications and then dropped off immediately. We wanted to create something that gave them a reason to stay, a healthcare assistant that was genuinely useful, trustworthy, and engaging.\n\nAs a Product Manager, my role was not to build everything myself but to work side by side with design, engineering, compliance, and data teams. I focused on translating patient needs into features we could safely deliver, aligning technical possibilities with product flows that made sense for real users.",
          problem: "We quickly realized that building a healthcare AI was not just about what the model could do, it was about whether patients trusted it. Through research and testing, the core problems became clear:\n\n• Generic answers ignored age, state, or medication history\n• Conversations had no memory, breaking flow and credibility\n• Pharmacies still carried the burden of answering repetitive questions\n• Models risked hallucinations and unsafe responses\n• Without trust or personalization, patients were not coming back\n\nThe insight was simple but powerful: Mira AI needed to be safe, personal, and coherent across multiple turns of conversation.",
          process: "My first focus was helping the team evaluate different models against real healthcare scenarios. Together we tested O3, O4-mini, and Grok. The outcome was a hybrid strategy, using O3 for accuracy and O4-mini for speed.\n\nFrom there, I worked with the team to design a three-layer prompt system that became our foundation:\n\n1. System role and safety guardrails\n2. Patient context injection (age, location, medications)\n3. User input\n\nThis gave us a safer and more testable structure for healthcare conversations.\n\nFor the MVP launch, my role was to bridge technical capabilities with patient needs. Working cross-functionally, I supported the team in building and validating features such as:\n\n• Session memory, so conversations felt continuous\n• Clarification prompts, to handle vague inputs gracefully\n• Personalization, by safely integrating HIPAA-compliant patient data\n• Feedback capture, through thumbs up and down with sentiment tracking\n• Conversational UX, with smoother animations and clear error states\n• Event tracking, by setting up dashboards to measure engagement and feedback",
          solution: "Together, we created Mira AI, a healthcare assistant built around safety, personalization, and conversational continuity.\n\n**Technical foundation:**\n• Three-layer prompt system with guardrails\n• Session memory for multi-turn continuity\n• Multi-model approach (O3 and O4-mini)\n• Real-time feedback and monitoring\n\n**User experience:**\n• Personalized responses grounded in patient context\n• Clarification prompts for ambiguous questions\n• Intuitive, empathetic conversational flow\n• A clean chat interface with clear error handling\n\n**Safety and compliance:**\n• Guardrails to reduce hallucinations\n• HIPAA-compliant data handling\n• Escalation paths to human support when needed",
          outcome: "We launched the Mira AI MVP to randomized patient groups with clear success metrics:\n\n• Engagement: at least two messages per session\n• Retention: at least 50 percent repeat users\n• Safety: at least 95 percent context accuracy\n• Latency: target response time under two seconds, down from an 11 second baseline\n\nEarly results showed promise, but also surfaced opportunities. Handoffs to human support were clunky, feedback capture was lower than expected, and response streaming needed to be faster.\n\n**What I learned:**\n• Safety is non-negotiable: strong guardrails matter as much as accuracy\n• Personalization builds trust: context-aware answers feel more credible\n• Memory drives retention: multi-turn conversations keep patients engaged\n• PMs amplify teams: my impact was not in building features directly, but in connecting design, engineering, compliance, and data into a cohesive product vision\n\nMira AI taught me how to navigate high-stakes AI work while balancing innovation with patient trust, safety, and long-term product value."
      }
    },
    {
      id: 2,
      title: "Reducing Pharmacy Hold Times with AI", 
      subtitle: "JiaBot",
      status: "SHIPPED • Jul 2025",
      gradient: "var(--gradient-blue-purple)",
      description: "JiaBot, shipped July 2025 ",
      company: "NimbleRx",
      role: "Product Manager/Product Designer/Data Analyst",
      timeline: "Jul 2025",
      team: "NimbleRx",
      skills: "AI/ML, Product Strategy, Chatbot Development",
      details: {
        intro: "You know that feeling when you call a pharmacy and get stuck on hold for what feels like forever, just to ask a simple question about your prescription? Behind the counter, pharmacists are overwhelmed by calls about refills, copays, and order status, questions that should be instant to answer.\n\nThis was the reality I faced during my internship at NimbleRx. Patients were frustrated waiting for answers, and pharmacists were drowning in routine inquiries. As the Product Manager of the team, my challenge was to improve JiaBot, our AI-powered patient support chatbot. The goal was simple: make it smart enough to resolve common questions upfront, and smooth enough that patients would actually want to use it.",
        problem: "We launched the first version of JiaBot with big ambitions. It included:\n\n• FAQ buttons for top questions\n• Keyword-based tagging to classify patient messages\n• Smart prompting to redirect or escalate with context\n• Data logging to track clicks and responses\n\nOn paper, it looked solid. In practice, adoption was low. Only 4 percent of patients tried JiaBot, and most dropped off before completing a chat. Escalations still went straight to pharmacy staff, and keyword matching often misclassified questions.\n\nThe lesson was clear: features alone do not guarantee impact. Adoption, clarity, and trust mattered more than technical capability.",
        process: "For the second milestone, I led the team in transforming JiaBot into a patient-friendly assistant. My role as Product Manager was to own the specs, define goals, and work closely with engineering and design to bring the improvements to life.\n\nWe introduced:\n\n• Smarter understanding by replacing brittle keyword matching with intent recognition models\n• Context-aware support cards tailored to the patient's state, such as showing refill details or delivery status up front\n• Simpler escalation where patients could type \"Talk to my pharmacist\" for a clean, contextual handoff\n• Cleaner UX with suggested questions, a clearer layout, and less friction in navigating the chat\n• A lightweight feedback loop so patients could rate responses and we could quickly learn what worked\n\nThe shift was clear. Instead of building features for their own sake, we focused on proving real patient impact.",
        solution: "The result was a smarter, more intuitive JiaBot.\n\n**Technical improvements:**\n• Intent recognition instead of keyword matching\n• Support cards that adapt to each patient's context\n• Smooth, contextual escalation paths\n• A simplified chat interface with suggested questions\n• Built-in feedback collection\n\n**User experience focus:**\n• Clear, actionable answers patients could trust\n• Low-friction conversation flow\n• Escalation when needed without confusion or dead ends\n• A design that prioritized ease of use over technical flash\n\nAs the Product Manager of the team, I ensured that every improvement balanced patient needs with pharmacy efficiency, while guiding engineering and design toward outcomes that mattered most.",
        outcome: "We set ambitious but measurable goals: reduce pharmacy escalations by 25 percent, resolve 75 percent of inquiries in the chatbot layer, and achieve a 60 percent or higher satisfaction rating. Early results showed encouraging progress, especially in resolution rates and patient engagement.\n\n**What I learned:**\n• Discoverability is half the battle: patients cannot use what they cannot see\n• Trust is fragile: one irrelevant response can push users back to live support\n• AI is only as strong as the experience around it: intent recognition worked, but only when paired with clear flows and design choices\n• Data tells the story: adoption and resolution metrics were the true compass for product decisions\n\nJiaBot showed me what product management is really about: leading a team, turning messy signals into actionable improvements, and creating solutions that make life easier for both patients and pharmacists."
      }
    },
    {
      id: 3,
      title: "Bringing Composting Back to Campus",
      subtitle: "Greensort Western", 
      status: "SHIPPED • Jan 2024",
      gradient: "var(--gradient-pink-orange)",
      description: "Greensort Western, shipped in Jan 2024",
      company: "Student Led Initiative",
      role: "Co-Founder/Product Manager/Product Designer",
      timeline: "Jan 2024",
      team: "Student Initiative",
      skills: "Sustainability, Product Strategy, Mobile Development",
      details: {
        intro: "When I arrived at Western University, I was shocked to discover that every piece of food waste generated on campus ended up in landfill. London, Ontario was the largest city in Canada without a green bin program, and despite students producing tons of organic waste across dining halls and residences, there was no composting system in place.\n\nIt was a frustrating reality. Students wanted to live sustainably, but the system gave them no way to do it. Surveys confirmed this sentiment: Western's waste management was rated just 3.7 out of 10, and many students were surprised and disappointed that composting options they had at home did not exist on campus.\n\nI could not accept this gap. So I co-founded GreenSort Western, a student-led initiative to bring composting back to campus. Our mission was simple but ambitious: reduce greenhouse gas emissions, improve waste sorting, and give students an accessible way to live sustainably. This was not just about waste management, it was about empowering students to make a real environmental impact.",
        problem: "Our research uncovered several obstacles:\n\n• No municipal green bin program in London, leaving students without options\n• Residences with kitchens generating large volumes of food waste that went to landfill\n• Contamination issues in existing bins, with food waste going into garbage and non-organics going into green bins\n• High student demand, but no infrastructure to support it\n\nThe breakthrough came when we realized the issue was not a lack of will. Students cared deeply about sustainability, but without infrastructure and education, they could not act on their values.",
        process: "Through surveys and conversations with student councils, housing staff, and sustainability mentors, we found three areas to focus on:\n\n• Awareness: Many students were unsure how to sort waste correctly\n• Infrastructure: Western had bins in storage but no plan to roll them out\n• Support: Key stakeholders, including Housing and the USC, were open to helping if we brought forward a workable plan\n\nWorking with a small team of students, we designed the GreenSort Western system with three components:\n\n1. Green Bin Rollout\n• Pilot launch in residences, then scaled across dorms with kitchens\n• Compostable bags and clear, visual signage to reduce contamination\n• Repurposed existing bins in storage to save costs\n\n2. Waste Sorting App\n• Integrated into Western's official student services app\n• Features included object recognition to scan waste items, gamification with rewards, and an education hub with sustainability resources\n• Direct reporting for missing bins or contamination issues\n\n3. Partnerships and Education\n• Collaborated with Western Housing, the USC, and local environmental groups\n• Student ambassadors promoted the program and taught peers proper sorting",
        solution: "We created GreenSort Western, a comprehensive composting system that combined physical infrastructure with digital support.\n\n**Physical infrastructure:**\n• Green bins across residences, with compostable bags and clear signage\n• Repurposed bins from storage to cut costs\n• Pilot in Bayfield residence before campus-wide rollout\n\n**Digital support:**\n• Sorting app integrated into Western's student app\n• Object recognition and gamification to encourage use\n• Education hub and sustainability resources\n• Reporting channels for missing bins or contamination\n\n**Community engagement:**\n• Partnerships with Housing, USC, and local groups\n• Student ambassadors driving awareness and education\n• Peer-led workshops to build a culture of sustainability",
        outcome: "**Wins:**\n• Successfully launched Western's first green bin program across residences\n• Integrated the GreenSort app into Western's official student app\n• Engaged students directly through ambassadors and workshops\n\n**What I learned:**\n• Framing matters: positioning London as \"the largest city in Canada without a green bin program\" made the problem impossible to ignore\n• Education and infrastructure must go hand in hand: bins alone do not work without clear signage and awareness\n• Leverage what already exists: repurposing bins and integrating into existing student apps kept costs low and sped up adoption\n• Start small to scale big: piloting in one residence built the credibility needed for a campus-wide rollout\n\nFor me, GreenSort Western proved that students can drive institutional change when they combine strategy, advocacy, and design."
      }
    },
    {
      id: 4,
      title: "Automating Workflows and Enabling AI Adoption in Consulting",
      subtitle: "KPMG",
      status: "SHIPPED • AUG 2024",
      gradient: "var(--gradient-blue-green)",
      description: "KPMG, shipped August 2024",
      company: "KPMG",
      role: "Consulting Intern",
      timeline: "Aug 2024",
      team: "KPMG",
      skills: "Python, VBA, AI Training, Process Automation",
      details: {
        intro: "During my internship at KPMG, I noticed a clear pattern: consultants were spending late nights manually pulling access data, cross-checking permissions, and formatting reports that should have taken minutes, not hours. Brilliant people were stuck doing repetitive work while higher-value client analysis waited.\n\nAt the same time, the firm was rolling out its own AI tools, including Microsoft Copilot, but adoption was low. Many team members did not know how to use them or where they could add value. I started asking a simple question: \"What do you hate most about the job?\" The answers revealed a long list of inefficiencies and sparked my drive to find better ways of working.\n\nI was not brought in to build tools, but that is exactly what I began doing. As a consultant on the team, I started small: identifying pain points, prototyping lightweight automations, and helping colleagues adopt the AI tools already available to them. It showed me that anyone who notices gaps can take the first step toward building a solution.",
        problem: "Through team interviews and observation, I identified three main challenges:\n\n• Manual workflows that consumed hours each week\n• Low adoption of AI tools due to lack of training and clear use cases\n• Inefficient reliance on SmartSheet and Excel without automation\n\nThe breakthrough was realizing that if consultants could save time on repetitive tasks, they could focus more energy on meaningful client analysis.",
        process: "As the product-minded member of the team, I took a two-pronged approach:\n\n1. Automating Workflows\n• Built Python scripts to automate repetitive data extraction and reporting tasks\n• Created a tool that instantly pulled user access data and highlighted sensitive privacy permissions\n• Used VBA and PowerShell to streamline SmartSheet and Excel reporting\n• Reduced project delivery times by an estimated 30 percent\n\n2. Enabling AI Adoption\n• Designed and ran workshops to teach consultants how to use KPMG's AI tools and Microsoft Copilot\n• Introduced prompt engineering techniques for real client use cases\n• Helped team members cut manual execution time from 15 hours to 5 hours per week",
        solution: "The end result was a combined approach of automation and enablement:\n\n**Technical automation:**\n• Python tools for data analysis and reporting\n• VBA and PowerShell scripts to reduce Excel and SmartSheet friction\n• Streamlined workflows that cut down on repetitive tasks\n\n**AI enablement:**\n• Training sessions to increase confidence with internal AI tools\n• Practical demonstrations of Copilot and AI use cases\n• Resources for the team to apply AI independently in client engagements",
        outcome: "The impact was clear:\n\n• Delivery times dropped by 30 percent\n• Each consultant saved around 10 hours a week on repetitive tasks\n• Manual errors decreased with automation\n• AI adoption across the team improved significantly\n\nThis was my first real experience building technical solutions in a business environment. I learned that curiosity drives impact: simply asking \"What frustrates you?\" uncovered the biggest opportunities for change. I also saw how even small scripts could unlock significant efficiency, and how teaching others multiplied my impact far beyond what I could do myself.\n\nMost importantly, KPMG showed me that product management is not always about building external products for customers. Sometimes it starts with noticing inefficiencies around you and building internal solutions that make teams work smarter, not harder."
      }
    },
    {
      id: 5,
      title: "Giving Every Child a Voice Through Music",
      subtitle: "Duet",
      status: "CREATED • OCT 2024",
      gradient: "var(--gradient-purple-pink)",
      description: "Cal Hacks 11.0, created Oct 2024",
      company: "Cal Hacks 11.0",
      role: "Product Designer/Frontend Developer",
      timeline: "Oct 2024",
      team: "Hackathon Team (",
      skills: "Python, Next.js, AI/ML, EEG Technology",
      details: {
        intro: "Duet's music generation reimagines how we approach music therapy. By capturing real-time brainwave data using Emotiv EEG headsets, we translate neural signals into dynamic, personalized soundscapes. Backed by machine learning, our platform classifies emotional states and generates adaptive music that evolves with the mind. At its core, Duet is about making creativity accessible. We are all intrinsically creative, but some, whether because of language or developmental barriers, struggle to convey it. Duet brings together art, neuroscience, and technology to let that creativity shine.\n\nOne in ten children in the United States has a developmental disability, and many do not have the tools to express themselves through traditional means. My teammate Justin and I had taught music to children for years, and we saw firsthand how non-verbal students were excluded from opportunities to share their creativity. That experience inspired our hackathon team of four to take on this challenge at Cal Hacks.\n\nThe problem was clear: brilliant, creative children had emotions and ideas they could not express. We asked ourselves, what if we could translate brainwaves into music in real time? Could we create a way for every child to have a voice through sound?",
        problem: "We identified four core challenges facing children with developmental disabilities:\n\n• Limited tools for creative expression beyond traditional means\n• Non-verbal students excluded from music and art opportunities\n• Difficulty communicating emotions and ideas through conventional methods\n• Lack of accessible technology that could bridge the gap between mind and music\n\nThe key insight was simple: if we could create a direct pathway from brainwaves to music, children who couldn't use words or instruments could still express their creativity and emotions through sound.",
        process: "Over the course of the hackathon, our team researched EEG technology, music therapy principles, and generative AI. We spent days experimenting with Emotiv EEG headsets that streamed brainwave activity in real time, then built an end-to-end system that could transform those signals into music.\n\nOur technical approach:\n\n• A Python backend, using the Cortex library, to process EEG brainwave signals\n• A SingleStore database for ultra-low-latency processing so the system could react instantly\n• A live AI \"composer\" powered by Google Gemini that generated music based on emotional state, available instruments, and what it had just played\n• Sonic Pi, a Ruby-based music library, to perform live generation of adaptive soundscapes\n• A Next.js frontend that I built to visualize brainwave activity and show how signals connected to the music in real time\n\nThe biggest challenge was designing true live AI music generation. Traditional systems either hard-code music rules or generate static pieces offline. We wanted an AI that could make creative decisions on the fly. At first it seemed impossible, but through collaboration and rapid iteration, we discovered a method that worked. Hardware integration also tested our patience, since none of us had prior experience with EEGs, but solving those problems became one of the most rewarding aspects of the project.",
        solution: "The result was Duet, a brain-computer interface that lets children hear their inner world as music.\n\n**Core technology:**\n• Python backend with Cortex library for EEG signal processing\n• SingleStore database for ultra-low-latency real-time processing\n• Google Gemini AI composer for adaptive music generation\n• Sonic Pi Ruby library for live sound synthesis\n• Next.js frontend for brainwave and music visualization\n\n**User experience:**\n• A child wears an EEG headset, and their brainwaves are captured in real time\n• The system interprets focus and relaxation states, adjusting tempo, rhythm, and intensity\n• An AI composer generates adaptive music on the fly\n• The frontend I built visualizes both the brainwaves and the music, creating a multisensory experience\n\nFor the first time, children who could not use words or instruments had a way to express themselves through sound.",
        outcome: "The impact was immediate. Ninety-seven percent of demo users said they would use Duet again. Our project won First Place Grand Prize at Cal Hacks 11.0.\n\n**What I learned:**\n• Innovation comes from persistence, even when the idea feels impossible\n• Social impact can fuel creativity and keep a team motivated through late-night debugging\n• The power of collaboration: with a team of four combining diverse skills, and with Justin and me contributing our background in music teaching, we created something none of us could have built alone\n• Hardware integration teaches patience and problem-solving skills\n• Real-time AI generation requires careful balance between creativity and technical constraints\n\nDuet gave children a voice where they had none, and it reminded me why I build: to make technology meaningful, accessible, and human."
      }
    },
    {
      id: 6,
      title: "Bridging Sustainable Design and Environmental Reality",
      subtitle: "SolarScope",
      status: "CREATED • NOV 2024",
      gradient: "var(--gradient-green-blue)",
      description: "Hack Western 10.0, created Nov 2024",
      company: "Hack Western 10.0",
      role: "Full-Stack Developer/Frontend Developer",
      timeline: "Nov 2024",
      team: "Hackathon Team",
      skills: "Swift, Python, AR/VR, Computer Vision",
      details: {
        what: "AR application that visualizes solar panel installations on existing buildings using computer vision",
        problem: "Property owners struggle to envision solar panel installations and their potential impact",
        process: "Developed computer vision for building analysis, created AR visualization tools, and integrated solar efficiency calculations",
        solution: "Mobile AR app that overlays realistic solar panel visualizations on buildings with efficiency predictions",
        outcome: "Successfully demonstrated at hackathon with 90% accuracy in solar panel placement recommendations"
      }
    }
  ];

  return (
    <section className="py-24 px-6 md:px-12 lg:px-24">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-light mb-16">Cool Projects I've Built</h2>
        
        <div className="grid md:grid-cols-2 gap-8">
          {projects.map((project, index) => {
            const cardRef = useRef(null);
            const cardInView = useInView(cardRef, { once: true, amount: 0.2 });
            
            return (
              <motion.div
                key={index}
                ref={cardRef}
                initial={{ opacity: 0, y: 50 }}
                animate={cardInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
                transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
              >
                <Dialog>
              <DialogTrigger asChild>
                <Card className="group cursor-pointer hover:shadow-lg transition-all duration-300 border-0 overflow-hidden">
                  <div 
                    className="h-48 bg-cover bg-center bg-no-repeat"
                    style={{ 
                      backgroundImage: project.subtitle === "Mira AI" 
                        ? `url(/MiraAI.jpg)`
                        : project.subtitle === "JiaBot"
                        ? `url(/JiaBot.png)`
                        : project.subtitle === "Greensort Western"
                        ? `url(/WesternGreensort.jpg)`
                        : project.subtitle === "KPMG"
                        ? `url(/KPMG.png)`
                        : project.subtitle === "Duet"
                        ? `url(/Duet.png)`
                        : project.subtitle === "SolarScope"
                        ? `url(/SolarScope.png)`
                        : `url(/${project.subtitle.toLowerCase().replace(/\s+/g, '')}.png)`,
                    }}
                  >
                  </div>
                  <CardContent className="p-6">
                    <div className="mb-4">
                      <h3 className="text-xl font-medium mb-2">{project.subtitle}</h3>
                      <Badge variant="outline" className="text-xs mb-2">
                        {project.status}
                      </Badge>
                      <p className="text-sm text-muted-foreground">{project.company}</p>
                    </div>
                    <p className="text-muted-foreground leading-relaxed">
                      {project.description}
                    </p>
                  </CardContent>
                </Card>
              </DialogTrigger>
              <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
                <div className="p-8">
                  <div className="space-y-8">
                    {/* PROJECT IMAGE - Full width, 256px */}
                    <div 
                      className="h-64 w-full rounded-lg bg-cover bg-center bg-no-repeat"
                      style={{ 
                        backgroundImage: project.subtitle === "Mira AI" 
                          ? `url(/MiraAI.jpg)`
                          : project.subtitle === "JiaBot"
                          ? `url(/JiaBot.png)`
                          : project.subtitle === "Greensort Western"
                          ? `url(/WesternGreensort.jpg)`
                          : project.subtitle === "KPMG"
                          ? `url(/KPMG.png)`
                          : project.subtitle === "Duet"
                          ? `url(/Duet.png)`
                          : project.subtitle === "SolarScope"
                          ? `url(/SolarScope.png)`
                          : `url(/${project.subtitle.toLowerCase().replace(/\s+/g, '')}.png)`,
                      }}
                    ></div>
                    
                    {/* PROJECT TITLE - Large, prominent */}
                    <h3 className="text-4xl font-bold">{project.title}</h3>
                    
                    {/* Role Information */}
                    <div className="bg-muted/10 p-4 rounded-lg">
                      <div className="text-sm text-muted-foreground">
                        <strong>Role:</strong> {project.role} • <strong>Timeline:</strong> {project.timeline} • <strong>Team:</strong> {project.team} • <strong>Skills:</strong> {project.skills}
                      </div>
                  </div>
                  
                    {/* Full story content */}
                    <div className="space-y-10">
                      <div>
                        <div className="text-lg leading-8 whitespace-pre-line" dangerouslySetInnerHTML={{__html: (project.details.intro || project.details.what || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}}></div>
                        </div>
                      
                      <div>
                        <h4 className="text-2xl font-bold mb-6">Understanding the Problem</h4>
                        <div className="text-lg leading-8 whitespace-pre-line" dangerouslySetInnerHTML={{__html: (project.details.problem || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}}></div>
                        </div>
                      
                      <div>
                        <h4 className="text-2xl font-bold mb-6">The Journey</h4>
                        <div className="text-lg leading-8 whitespace-pre-line" dangerouslySetInnerHTML={{__html: (project.details.process || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}}></div>
                        </div>
                      
                      <div>
                        <h4 className="text-2xl font-bold mb-6">The Solution</h4>
                        <div className="text-lg leading-8 whitespace-pre-line" dangerouslySetInnerHTML={{__html: (project.details.solution || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}}></div>
                        </div>
                      
                      <div>
                        <h4 className="text-2xl font-bold mb-6">Reflection</h4>
                        <div className="text-lg leading-8 whitespace-pre-line" dangerouslySetInnerHTML={{__html: (project.details.outcome || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}}></div>
                          </div>
                        </div>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Projects;