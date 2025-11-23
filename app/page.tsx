import Link from "next/link"
import { AnimatedBackground } from "@/components/animated-background"
import { Button } from "@/components/ui/button"
import { Calendar, Sparkles, Zap, Clock, Target, Brain } from "lucide-react"

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <AnimatedBackground />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6">
        <div className="max-w-5xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-sm text-primary mb-4">
            <Sparkles className="w-4 h-4" />
            AI-Powered Task Management
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-balance">
            Plan Your Day, <span className="text-primary">Powered by AI</span>
          </h1>

          <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto text-balance">
            PlanItOut intelligently organizes your tasks based on priority, deadlines, and your schedule. Let AI handle
            the planning while you focus on getting things done.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <Link href="/dashboard">
              <Button size="lg" className="text-lg px-8 py-6">
                Get Started
                <Sparkles className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8 py-6 bg-transparent">
              Watch Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Smart Features for Busy People</h2>
            <p className="text-xl text-muted-foreground">Everything you need to stay organized and productive</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="p-6 rounded-lg bg-card border border-border hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI Task Sorting</h3>
              <p className="text-muted-foreground">
                Automatically organize tasks by importance and deadline with one click
              </p>
            </div>

            <div className="p-6 rounded-lg bg-card border border-border hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Drag & Drop Calendar</h3>
              <p className="text-muted-foreground">Easily schedule tasks by dragging them onto your calendar</p>
            </div>

            <div className="p-6 rounded-lg bg-card border border-border hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Priority Based</h3>
              <p className="text-muted-foreground">Rate tasks from 1-10 and let AI schedule them optimally</p>
            </div>

            <div className="p-6 rounded-lg bg-card border border-border hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI Chatbot</h3>
              <p className="text-muted-foreground">Add tasks naturally through conversation with our AI assistant</p>
            </div>

            <div className="p-6 rounded-lg bg-card border border-border hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Clock className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Time Estimates</h3>
              <p className="text-muted-foreground">Track how long tasks take and plan your day accordingly</p>
            </div>

            <div className="p-6 rounded-lg bg-card border border-border hover:border-primary/50 transition-colors">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Smart Notifications</h3>
              <p className="text-muted-foreground">Get reminded about upcoming tasks at the right time</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-24 px-6">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-4xl md:text-5xl font-bold text-balance">Ready to Take Control of Your Day?</h2>
          <p className="text-xl text-muted-foreground">
            Join thousands of users who have transformed their productivity with PlanItOut
          </p>
          <Link href="/dashboard">
            <Button size="lg" className="text-lg px-8 py-6">
              Start Planning Now
              <Sparkles className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-border py-12 px-6">
        <div className="max-w-6xl mx-auto text-center text-muted-foreground">
          <p>&copy; 2025 PlanItOut. All rights reserved.</p>
        </div>
      </footer>
    </main>
  )
}
