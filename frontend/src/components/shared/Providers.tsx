"use client";

import { NextUIProvider } from "@nextui-org/react";
import { ReactNode, useEffect } from "react";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { fetchCurrentUser } from "@/lib/auth";
import { useAuthStore } from "@/hooks/useAuth";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const initialized = useAuthStore((state) => state.initialized);

  useEffect(() => {
    if (initialized) {
      return;
    }

    void fetchCurrentUser();
  }, [initialized]);

  return (
    <NextUIProvider>
      {children}
      <ToastContainer position="bottom-right" theme="dark" />
    </NextUIProvider>
  );
}
