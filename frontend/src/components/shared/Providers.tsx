"use client";

import { NextUIProvider } from "@nextui-org/react";
import { ReactNode, useEffect, useRef } from "react";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { fetchCurrentUser } from "@/lib/auth";
import { useAuthStore } from "@/hooks/useAuth";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const initialized = useAuthStore((state) => state.initialized);

  const hasFetchedRef = useRef(false);

  useEffect(() => {
    if (initialized || hasFetchedRef.current) {
      return;
    }

    hasFetchedRef.current = true;
    void fetchCurrentUser();
  }, [initialized]);

  return (
    <NextUIProvider>
      {children}
      <ToastContainer position="bottom-right" theme="dark" />
    </NextUIProvider>
  );
}
