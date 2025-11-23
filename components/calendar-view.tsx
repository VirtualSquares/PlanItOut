"use client"

import type React from "react"

import { useState } from "react"
import type { Task } from "./task-calendar"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Clock, CalendarIcon } from "lucide-react"
import { format, addDays, startOfWeek, addHours } from "date-fns"
import { cn } from "@/lib/utils"

type CalendarViewProps = {
  tasks: Task[]
  viewMode: "day" | "week" | "month"
  onUpdateTask: (id: string, updates: Partial<Task>) => void
}

export function CalendarView({ tasks, viewMode, onUpdateTask }: CalendarViewProps) {
  const [dragOverSlot, setDragOverSlot] = useState<string | null>(null)

  const today = new Date()
  const weekStart = startOfWeek(today, { weekStartsOn: 0 })

  const getImportanceColor = (importance: number) => {
    if (importance >= 8) return "border-l-destructive bg-destructive/5"
    if (importance >= 6) return "border-l-warning bg-warning/5"
    if (importance >= 4) return "border-l-primary bg-primary/5"
    return "border-l-muted-foreground bg-muted/30"
  }

  const handleDragOver = (e: React.DragEvent, slotId: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "move"
    setDragOverSlot(slotId)
  }

  const handleDragLeave = () => {
    setDragOverSlot(null)
  }

  const handleDrop = (e: React.DragEvent, date: Date, hour?: number) => {
    e.preventDefault()
    setDragOverSlot(null)

    try {
      const taskData = JSON.parse(e.dataTransfer.getData("application/json")) as Task
      const scheduledTime = new Date(date)
      if (hour !== undefined) {
        scheduledTime.setHours(hour, 0, 0, 0)
      }
      onUpdateTask(taskData.id, { scheduledTime })
    } catch (error) {
      console.error("Error dropping task:", error)
    }
  }

  const hours = Array.from({ length: 14 }, (_, i) => i + 7) // 7 AM to 8 PM

  if (viewMode === "week") {
    const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))

    return (
      <ScrollArea className="flex-1">
        <div className="p-6">
          <div className="grid grid-cols-8 gap-4">
            {/* Time column */}
            <div className="space-y-16">
              <div className="h-12" /> {/* Header spacer */}
              {hours.map((hour) => (
                <div key={hour} className="text-xs text-muted-foreground h-20 flex items-start">
                  {format(addHours(new Date().setHours(hour, 0, 0, 0), 0), "h a")}
                </div>
              ))}
            </div>

            {/* Days columns */}
            {weekDays.map((day) => (
              <div key={day.toISOString()} className="space-y-2">
                <div className="h-12 flex flex-col items-center justify-center border-b border-border">
                  <span className="text-xs text-muted-foreground font-medium">{format(day, "EEE")}</span>
                  <span
                    className={cn(
                      "text-lg font-semibold",
                      format(day, "yyyy-MM-dd") === format(today, "yyyy-MM-dd") && "text-primary",
                    )}
                  >
                    {format(day, "d")}
                  </span>
                </div>

                <div className="space-y-16">
                  {hours.map((hour) => {
                    const slotId = `${format(day, "yyyy-MM-dd")}-${hour}`
                    const hourTasks = tasks.filter((task) => {
                      if (!task.scheduledTime) return false
                      return (
                        format(task.scheduledTime, "yyyy-MM-dd") === format(day, "yyyy-MM-dd") &&
                        task.scheduledTime.getHours() === hour
                      )
                    })

                    return (
                      <div
                        key={hour}
                        onDragOver={(e) => handleDragOver(e, slotId)}
                        onDragLeave={handleDragLeave}
                        onDrop={(e) => handleDrop(e, day, hour)}
                        className={cn(
                          "min-h-[80px] border-t border-border/50 pt-1 transition-colors rounded-md",
                          dragOverSlot === slotId && "bg-primary/10 border-primary",
                        )}
                      >
                        {hourTasks.map((task) => (
                          <Card
                            key={task.id}
                            className={cn(
                              "p-2 mb-1 border-l-4 cursor-pointer hover:shadow-md transition-all",
                              getImportanceColor(task.importance),
                              task.completed && "opacity-50",
                            )}
                            onClick={() => onUpdateTask(task.id, { completed: !task.completed })}
                          >
                            <h4 className="font-medium text-xs line-clamp-1">{task.title}</h4>
                            <div className="flex items-center gap-1 mt-1">
                              <Clock className="h-3 w-3 text-muted-foreground" />
                              <span className="text-xs text-muted-foreground">{task.estimatedTime}m</span>
                            </div>
                          </Card>
                        ))}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </ScrollArea>
    )
  }

  // Simplified day/month view - showing task list
  return (
    <ScrollArea className="flex-1">
      <div className="p-6 max-w-4xl mx-auto">
        <div className="space-y-3">
          {tasks.map((task) => (
            <Card
              key={task.id}
              className={cn(
                "p-4 border-l-4 cursor-pointer hover:shadow-md transition-all",
                getImportanceColor(task.importance),
                task.completed && "opacity-50",
              )}
              onClick={() => onUpdateTask(task.id, { completed: !task.completed })}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h3 className={cn("font-semibold text-lg", task.completed && "line-through")}>{task.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{task.description}</p>
                  <div className="flex items-center gap-3 mt-3 flex-wrap">
                    <Badge variant="outline">Priority: {task.importance}/10</Badge>
                    {task.estimatedTime && (
                      <Badge variant="outline">
                        <Clock className="h-3 w-3 mr-1" />
                        {task.estimatedTime}m
                      </Badge>
                    )}
                    {task.category && <Badge variant="secondary">{task.category}</Badge>}
                    {task.dueDate && (
                      <Badge variant="outline">
                        <CalendarIcon className="h-3 w-3 mr-1" />
                        {format(task.dueDate, "MMM d")}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </ScrollArea>
  )
}
