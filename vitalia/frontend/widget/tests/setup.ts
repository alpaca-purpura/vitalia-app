/**
 * Vitest setup for widget tests.
 * Provides @testing-library/react matchers.
 */
import * as matchers from "@testing-library/jest-dom/matchers";
import { expect } from "vitest";
expect.extend(matchers);
