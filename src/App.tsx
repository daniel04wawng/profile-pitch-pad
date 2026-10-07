import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";
import Landing from "./pages/Landing";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

// The café loads behind the landing page (which preloads it), and opens directly at /cafe.
const Cafe = lazy(() => import("./pages/Cafe"));
// the old one-page portfolio, kept out of the way
const Index = lazy(() => import("./pages/Index"));

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route
            path="/classic"
            element={
              <Suspense fallback={<div className="h-[100dvh] bg-white" />}>
                <Index />
              </Suspense>
            }
          />
          <Route
            path="/cafe"
            element={
              <Suspense fallback={<div className="h-[100dvh] bg-[#f2dfcc]" />}>
                <Cafe />
              </Suspense>
            }
          />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
