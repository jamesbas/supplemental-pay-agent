"use client"

import { useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { FiUser, FiDollarSign, FiUsers, FiZap } from "react-icons/fi"

export default function HomePage() {
  const router = useRouter()
  const [selectedRole, setSelectedRole] = useState<string | null>(null)

  const handleRoleSelect = (role: string) => {
    setSelectedRole(role)
    router.push(`/chat?role=${role}`)
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-border">
        <div className="container flex h-16 items-center px-4 sm:px-8">
          <div className="flex items-center gap-2">
            <Image 
              src="/dxc-logo.svg"
              alt="DXC Logo"
              width={40}
              height={40}
              className="dark:invert"
            />
            <span className="text-lg font-semibold tracking-tight">
              DXC Supplemental Pay AI
            </span>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="container flex flex-col items-center justify-center px-4 py-16 md:py-24">
          <h1 className="text-center text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            DXC Supplemental Pay
            <span className="bg-gradient-to-r from-dxc-purple to-dxc-blue bg-clip-text text-transparent">
              {" "}AI Agent
            </span>
          </h1>
          <p className="mt-4 max-w-2xl text-center text-muted-foreground">
            Select your role to interact with the appropriate agent for analyzing
            supplemental pay data, policies, and recommendations.
          </p>
          <div className="mt-12 grid w-full max-w-3xl grid-cols-1 gap-6 sm:grid-cols-3">
            <RoleCard
              title="HR Team"
              description="Access and interpret DXC pay policies"
              icon={<FiUser className="h-8 w-8" />}
              onClick={() => handleRoleSelect("hr")}
              selected={selectedRole === "hr"}
            />
            <RoleCard
              title="People Manager"
              description="Calculate pay and get approval recommendations"
              icon={<FiUsers className="h-8 w-8" />}
              onClick={() => handleRoleSelect("manager")}
              selected={selectedRole === "manager"}
            />
            <RoleCard
              title="Payroll Manager"
              description="Analyze trends, outliers, and compliance"
              icon={<FiDollarSign className="h-8 w-8" />}
              onClick={() => handleRoleSelect("payroll")}
              selected={selectedRole === "payroll"}
            />
            <div className="col-span-1 sm:col-span-3 flex justify-center">
              <div className="w-full sm:w-1/3">
                <RoleCard
                  title="Intelligent Supplemental Pay"
                  description="Intelligent Agent for All questions on Supplemental Pay"
                  icon={<FiZap className="h-8 w-8" />}
                  onClick={() => handleRoleSelect("intelligent")}
                  selected={selectedRole === "intelligent"}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
      <footer className="border-t border-border py-6">
        <div className="container flex flex-col items-center justify-center gap-4 px-4 text-center text-sm text-muted-foreground">
          <p>
            © {new Date().getFullYear()} DXC Technology. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

interface RoleCardProps {
  title: string
  description: string
  icon: React.ReactNode
  onClick: () => void
  selected: boolean
}

function RoleCard({ title, description, icon, onClick, selected }: RoleCardProps) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center rounded-lg border border-border bg-card p-6 text-center shadow-sm transition-all hover:border-primary hover:shadow-md ${
        selected ? "border-primary bg-primary/5 ring-2 ring-primary/20" : ""
      }`}
    >
      <div className="mb-4 rounded-full bg-primary/10 p-3 text-primary">
        {icon}
      </div>
      <h3 className="text-xl font-medium">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </button>
  )
} 