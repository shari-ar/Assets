"use client";

import Link from "next/link";
import { Card, CardBody, Chip } from "@nextui-org/react";
import { AppButton } from "@/components/ui/AppButton";
import { heroGradient } from "@/styles/theme";

export default function HomePage() {
  return (
    <section className="flex flex-col gap-12">
      <div
        className={`glass-panel mx-auto flex max-w-4xl flex-col items-center gap-6 px-8 py-14 text-center bg-gradient-to-br ${heroGradient}`}
      >
        <Chip color="primary" variant="flat">
          Activate Architecture Shell
        </Chip>
        <h1 className="text-4xl font-semibold leading-tight md:text-5xl">
          Assets Platform brings lending, wallets, and reporting together.
        </h1>
        <p className="text-lg text-default-400 md:text-xl">
          Launch faster with our Django Ninja API and Next.js dashboard starter.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <AppButton as={Link} href="/auth/register" size="lg">
            Get Started
          </AppButton>
          <AppButton as={Link} href="/dashboard" size="lg" variant="bordered">
            View Dashboard
          </AppButton>
        </div>
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        {[
          {
            title: "Wallet Monitoring",
            description: "Track balances, settlements, and payouts in real time.",
          },
          {
            title: "Ticket Automation",
            description: "Approve, settle, and audit the entire lending journey.",
          },
          {
            title: "Insights",
            description: "Visualize KPIs across assets, teams, and payment partners.",
          },
        ].map((feature) => (
          <Card key={feature.title} className="border border-default-200/50 bg-background/60">
            <CardBody className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm text-default-400">{feature.description}</p>
            </CardBody>
          </Card>
        ))}
      </div>
    </section>
  );
}
