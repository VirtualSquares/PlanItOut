import { TaskCalendar } from "@/components/task-calendar"
import { AnimatedBackground } from "@/components/animated-background"

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-background">
      <AnimatedBackground />
      <TaskCalendar />
    </main>
  )
}
