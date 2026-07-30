// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: vitalia-fase1-s0-TBD
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
