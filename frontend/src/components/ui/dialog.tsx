'use client'

import * as React from 'react'
import { X } from 'lucide-react'
import { Button } from './button'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

interface DialogContentProps {
  children: React.ReactNode
  className?: string
}

const DialogContext = React.createContext<{
  open: boolean
  onOpenChange: (open: boolean) => void
}>({
  open: false,
  onOpenChange: () => {},
})

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        onOpenChange(false)
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [open, onOpenChange])

  if (!open) return null

  return (
    <DialogContext.Provider value={{ open, onOpenChange }}>
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div
          className="fixed inset-0 bg-black/50"
          onClick={() => onOpenChange(false)}
        />
        {children}
      </div>
    </DialogContext.Provider>
  )
}

export function DialogContent({ children, className = '' }: DialogContentProps) {
  const { onOpenChange } = React.useContext(DialogContext)

  return (
    <div
      className={`relative z-50 w-full max-w-lg bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}
      onClick={(e) => e.stopPropagation()}
    >
      <button
        onClick={() => onOpenChange(false)}
        className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 dark:ring-offset-gray-950 dark:focus:ring-gray-300"
      >
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </button>
      {children}
    </div>
  )
}

export function DialogHeader({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`flex flex-col space-y-1.5 text-center sm:text-left mb-4 ${className}`}>
      {children}
    </div>
  )
}

export function DialogTitle({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <h2 className={`text-lg font-semibold leading-none tracking-tight ${className}`}>
      {children}
    </h2>
  )
}

export function DialogDescription({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <p className={`text-sm text-gray-500 dark:text-gray-400 ${className}`}>
      {children}
    </p>
  )
}

export function DialogFooter({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2 mt-6 ${className}`}>
      {children}
    </div>
  )
}

