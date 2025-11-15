"use client";

import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button, Avatar } from "@nextui-org/react";
import NextLink from "next/link";
import { toast } from "react-toastify";
import { useShallow } from "zustand/react/shallow";

import { useAuthStore } from "@/hooks/useAuth";
import { APP_NAME } from "@/lib/config";
import { logout } from "@/lib/auth";

export function AppNavbar() {
  const { user, initialized } = useAuthStore(
    useShallow((state) => ({
      user: state.user,
      initialized: state.initialized,
    })),
  );

  const avatarLabel = user
    ? (user.fullName
        ? user.fullName
            .split(" ")
            .filter(Boolean)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase())
            .join("")
        : user.email.slice(0, 2).toUpperCase())
    : "";

  const roleLabel = user?.role === "admin" ? "Admin" : "Member";

  return (
    <Navbar maxWidth="xl" position="sticky" className="bg-background/60 backdrop-blur">
      <NavbarBrand className="font-semibold text-large">
        <Link as={NextLink} href="/" color="foreground">
          {APP_NAME}
        </Link>
      </NavbarBrand>
      <NavbarContent className="hidden gap-4 sm:flex" justify="center">
        <NavbarItem>
          <Link as={NextLink} href="/dashboard" color="foreground">
            Dashboard
          </Link>
        </NavbarItem>
        <NavbarItem>
          <Link as={NextLink} href="/wallet" color="foreground">
            Wallet
          </Link>
        </NavbarItem>
        <NavbarItem>
          <Link as={NextLink} href="/tickets" color="foreground">
            Tickets
          </Link>
        </NavbarItem>
        <NavbarItem>
          <Link as={NextLink} href="/admin" color="foreground">
            Admin
          </Link>
        </NavbarItem>
      </NavbarContent>
      <NavbarContent justify="end">
        {user ? (
          <>
            <NavbarItem className="hidden items-center gap-2 sm:flex">
              <div className="hidden flex-col text-right sm:flex">
                <span className="text-sm font-medium text-foreground">{user.fullName || user.email}</span>
                <span className="text-xs uppercase tracking-wide text-default-500">{roleLabel}</span>
              </div>
              <Avatar
                className="bg-primary/20 text-primary"
                name={avatarLabel}
                showFallback
                size="sm"
              />
            </NavbarItem>
            <NavbarItem>
              <Button
                size="sm"
                variant="flat"
                onClick={async () => {
                  try {
                    await logout();
                    toast.info("Signed out");
                  } catch {
                    toast.error("Unable to logout. Please retry.");
                  }
                }}
              >
                Logout
              </Button>
            </NavbarItem>
          </>
        ) : initialized ? (
          <NavbarItem>
            <Button as={NextLink} color="primary" href="/auth/login" size="sm">
              Sign in
            </Button>
          </NavbarItem>
        ) : null}
      </NavbarContent>
    </Navbar>
  );
}
