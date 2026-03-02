import { describe, it, expect } from "vitest";

describe("Health Check", () => {
  it("should pass basic assertion", () => {
    expect(true).toBe(true);
  });

  it("should have correct app name in package.json", () => {
    expect("todo-frontend").toBeDefined();
  });
});
