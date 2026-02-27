import { describe, it, expect } from "vitest";

describe("${{ values.serviceName }}", () => {
  it("should have a valid service name", () => {
    const name = "${{ values.serviceName }}";
    expect(name).toBeTruthy();
    expect(name).toMatch(/^[a-z][a-z0-9-]*$/);
  });

  it("should have a valid port", () => {
    const port = parseInt("${{ values.port }}", 10);
    expect(port).toBeGreaterThan(0);
    expect(port).toBeLessThan(65536);
  });
});
