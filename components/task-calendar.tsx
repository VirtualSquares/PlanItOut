"use client"

import { useState } from "react"
import { CalendarView } from "./calendar-view"
import { TaskSidebar } from "./task-sidebar"
import { AIChatbot } from "./ai-chatbot"
import { Notifications } from "./notifications"
import { Button } from "@/components/ui/button"
import { Menu, Sparkles } from "lucide-react"

export type Task = {
  id: string
  title: string
  description: string
  importance: number
  estimatedTime: number
  dueDate?: Date
  completed: boolean
  category?: string
  aiSuggested?: boolean
  scheduledTime?: Date
}

export function TaskCalendar() {
  const [tasks, setTasks] = useState<Task[]>([
    {
      id: "1",
      title: "Complete project proposal",
      description: "Finish the Q1 project proposal for the client meeting",
      importance: 9,
      estimatedTime: 120,
      dueDate: new Date(2025, 0, 24),
      completed: false,
      category: "Work",
      scheduledTime: new Date(2025, 0, 22, 9, 0),
    },
    {
      id: "2",
      title: "Review pull requests",
      description: "Review and merge pending PRs from the team",
      importance: 7,
      estimatedTime: 45,
      completed: false,
      category: "Work",
      scheduledTime: new Date(2025, 0, 22, 14, 0),
    },
    {
      id: "3",
      title: "Gym workout",
      description: "Leg day at the gym",
      importance: 5,
      estimatedTime: 60,
      completed: false,
      category: "Personal",
      scheduledTime: new Date(2025, 0, 22, 18, 0),
    },
  ])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [viewMode, setViewMode] = useState<"day" | "week" | "month">("week")

  const addTask = (newTask: Omit<Task, "id" | "completed">) => {
    const task: Task = {
      ...newTask,
      id: Date.now().toString(),
      completed: false,
    }
    setTasks([...tasks, task])
  }

  const updateTask = (id: string, updates: Partial<Task>) => {
    setTasks(tasks.map((task) => (task.id === id ? { ...task, ...updates } : task)))
  }

  const deleteTask = (id: string) => {
    setTasks(tasks.filter((task) => task.id !== id))
  }

  const sortTasksByAI = () => {
    // Sort tasks by importance (highest first), then by due date
    const sorted = [...tasks].sort((a, b) => {
      if (b.importance !== a.importance) {
        return b.importance - a.importance
      }
      if (a.dueDate && b.dueDate) {
        return a.dueDate.getTime() - b.dueDate.getTime()
      }
      return 0
    })

    // Schedule tasks on calendar based on their priority and due dates
    const scheduledTasks = sorted.map((task, index) => {
      if (task.completed || task.scheduledTime) {
        return task // Don't reschedule completed or already scheduled tasks
      }

      // Determine the target date based on due date or schedule progressively
      let targetDate = new Date()

      if (task.dueDate) {
        // Schedule high priority tasks earlier relative to due date
        const daysBeforeDue = Math.max(1, Math.ceil((10 - task.importance) / 2))
        targetDate = new Date(task.dueDate)
        targetDate.setDate(targetDate.getDate() - daysBeforeDue)
      } else {
        // If no due date, schedule starting from today based on index
        targetDate.setDate(targetDate.getDate() + Math.floor(index / 3))
      }

      // Set time based on priority (high priority gets morning slots)
      const hour = task.importance >= 8 ? 9 : task.importance >= 6 ? 13 : 15
      targetDate.setHours(hour, 0, 0, 0)

      return {
        ...task,
        scheduledTime: targetDate,
      }
    })

    setTasks(scheduledTasks)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <TaskSidebar
        open={sidebarOpen}
        tasks={tasks}
        onAddTask={addTask}
        onUpdateTask={updateTask}
        onDeleteTask={deleteTask}
        onSortTasks={sortTasksByAI}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden">
              <Menu className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Sparkles className="h-6 w-6 text-primary" />
                PlanItOut
              </h1>
              <p className="text-sm text-muted-foreground">Smart task prioritization</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex gap-1 border border-border rounded-lg p-1">
              <Button variant={viewMode === "day" ? "secondary" : "ghost"} size="sm" onClick={() => setViewMode("day")}>
                Day
              </Button>
              <Button
                variant={viewMode === "week" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("week")}
              >
                Week
              </Button>
              <Button
                variant={viewMode === "month" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("month")}
              >
                Month
              </Button>
            </div>
            <Notifications tasks={tasks} />
          </div>
        </header>

        {/* Calendar */}
        <CalendarView tasks={tasks} viewMode={viewMode} onUpdateTask={updateTask} />
      </div>

      {/* AI Chatbot */}
      <AIChatbot open={chatOpen} onOpenChange={setChatOpen} onAddTask={addTask} />
    </div>
  )
}
