'use client'

import * as React from 'react'
import { ChevronDown } from 'lucide-react'

interface SelectProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
  className?: string
}

interface SelectContentProps {
  children: React.ReactNode
}

interface SelectItemProps {
  value: string
  children: React.ReactNode
}

const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
}>({
  value: '',
  onValueChange: () => {},
  open: false,
  setOpen: () => {},
})

export function Select({ value, onValueChange, children, className = '' }: SelectProps) {
  const [open, setOpen] = React.useState(false)
  const selectRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
      <div ref={selectRef} className={`relative ${className}`}>
        {children}
      </div>
    </SelectContext.Provider>
  )
}

export function SelectTrigger({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  const { open, setOpen } = React.useContext(SelectContext)

  return (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:ring-offset-gray-950 dark:placeholder:text-gray-400 dark:focus:ring-gray-300 ${className}`}
    >
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </button>
  )
}

export function SelectValue({
  placeholder,
}: {
  placeholder?: string
}) {
  const { value } = React.useContext(SelectContext)
  return <span>{value || placeholder}</span>
}

export function SelectContent({ children }: SelectContentProps) {
  const { open, setOpen } = React.useContext(SelectContext)

  if (!open) return null

  return (
    <>
      <div
        className="fixed inset-0 z-40"
        onClick={() => setOpen(false)}
      />
      <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-md shadow-lg max-h-60 overflow-auto">
        {children}
      </div>
    </>
  )
}

export function SelectItem({ value, children }: SelectItemProps) {
  const { value: selectedValue, onValueChange, setOpen } = React.useContext(SelectContext)
  const isSelected = selectedValue === value

  return (
    <div
      onClick={() => {
        onValueChange(value)
        setOpen(false)
      }}
      className={`relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none hover:bg-gray-100 dark:hover:bg-gray-700 focus:bg-gray-100 dark:focus:bg-gray-700 ${
        isSelected ? 'bg-gray-100 dark:bg-gray-700' : ''
      }`}
    >
      {children}
    </div>
  )
}

