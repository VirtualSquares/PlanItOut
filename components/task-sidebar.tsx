"use client"

import type React from "react"

import { useState } from "react"
import type { Task } from "./task-calendar"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Plus, Sparkles, Clock, CheckCircle2, Circle } from "lucide-react"
import { AddTaskModal } from "./add-task-modal"
import { cn } from "@/lib/utils"

type TaskSidebarProps = {
  open: boolean
  tasks: Task[]
  onAddTask: (task: Omit<Task, "id" | "completed">) => void
  onUpdateTask: (id: string, updates: Partial<Task>) => void
  onDeleteTask: (id: string) => void
  onSortTasks: () => void
}

export function TaskSidebar({ open, tasks, onAddTask, onUpdateTask, onDeleteTask, onSortTasks }: TaskSidebarProps) {
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [sortAnimating, setSortAnimating] = useState(false)

  const handleSort = () => {
    setSortAnimating(true)
    onSortTasks()
    setTimeout(() => setSortAnimating(false), 500)
  }

  const getImportanceColor = (importance: number) => {
    if (importance >= 8) return "bg-destructive text-destructive-foreground"
    if (importance >= 6) return "bg-warning text-foreground"
    if (importance >= 4) return "bg-primary text-primary-foreground"
    return "bg-muted text-muted-foreground"
  }

  const handleDragStart = (e: React.DragEvent, task: Task) => {
    e.dataTransfer.effectAllowed = "move"
    e.dataTransfer.setData("application/json", JSON.stringify(task))
  }

  return (
    <>
      <aside
        className={cn(
          "border-r border-border bg-card transition-all duration-300 flex flex-col",
          open ? "w-80" : "w-0",
          "lg:w-80",
        )}
      >
        <div className="p-4 border-b border-border space-y-3">
          <Button onClick={() => setAddModalOpen(true)} className="w-full" size="lg">
            <Plus className="h-5 w-5 mr-2" />
            Add Task
          </Button>
          <Button onClick={handleSort} variant="outline" className="w-full bg-transparent">
            <Sparkles className="h-4 w-4 mr-2" />
            AI Sort Tasks
          </Button>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-2">
            <h3 className="font-semibold text-sm text-muted-foreground mb-3">All Tasks ({tasks.length})</h3>
            {tasks.map((task) => (
              <div
                key={task.id}
                draggable={!task.completed}
                onDragStart={(e) => handleDragStart(e, task)}
                className={cn(
                  "p-3 rounded-lg border border-border bg-background hover:bg-muted/50 transition-colors",
                  !task.completed && "cursor-move",
                  sortAnimating && "task-sorting",
                )}
              >
                <div className="flex items-start gap-3">
                  <button className="mt-0.5" onClick={() => onUpdateTask(task.id, { completed: !task.completed })}>
                    {task.completed ? (
                      <CheckCircle2 className="h-5 w-5 text-success" />
                    ) : (
                      <Circle className="h-5 w-5 text-muted-foreground" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <h4 className={cn("font-medium text-sm", task.completed && "line-through text-muted-foreground")}>
                      {task.title}
                    </h4>
                    <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{task.description}</p>
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <Badge className={cn("text-xs", getImportanceColor(task.importance))}>
                        Priority: {task.importance}
                      </Badge>
                      {task.estimatedTime && (
                        <Badge variant="outline" className="text-xs">
                          <Clock className="h-3 w-3 mr-1" />
                          {task.estimatedTime}m
                        </Badge>
                      )}
                      {task.category && (
                        <Badge variant="secondary" className="text-xs">
                          {task.category}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </aside>

      <AddTaskModal open={addModalOpen} onOpenChange={setAddModalOpen} onAdd={onAddTask} />
    </>
  )
}
