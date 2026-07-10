"use client";

import { useEffect } from "react";
import CTAButton from "@/components/CTAButton";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex-grow flex flex-col items-center justify-center px-6 py-20 text-center gap-6">
      <h2 className="font-outfit text-2xl font-bold text-zinc-200">
        Something went wrong!
      </h2>
      <p className="font-sans text-sm text-zinc-500 max-w-sm">
        An error occurred while loading this page. You can try reloading or returning home.
      </p>
      <div className="flex items-center gap-4">
        <CTAButton variant="primary" onClick={() => reset()} className="text-xs">
          Try again
        </CTAButton>
        <CTAButton variant="secondary" onClick={() => window.location.href = "/"} className="text-xs">
          Go Home
        </CTAButton>
      </div>
    </div>
  );
}
