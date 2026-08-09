import { expect, test } from "@playwright/test";

declare global {
  interface Window {
    __uiPerf?: {
      frames: number;
      longTasks: number[];
      startedAt: number;
      observer?: PerformanceObserver;
    };
  }
}

test("playback stays responsive while the full graph is visible", async ({ page }) => {
  let graphRequests = 0;
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/graph?")) graphRequests += 1;
  });
  await page.goto("/");
  await expect(page.locator(".leaflet-map")).toBeVisible();
  await page.evaluate(() => {
    const state = { frames: 0, longTasks: [] as number[], startedAt: performance.now(), observer: undefined as PerformanceObserver | undefined };
    const countFrame = () => {
      state.frames += 1;
      if (performance.now() - state.startedAt < 3_500) requestAnimationFrame(countFrame);
    };
    if ("PerformanceObserver" in window) {
      state.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) state.longTasks.push(entry.duration);
      });
      try { state.observer.observe({ entryTypes: ["longtask"] }); } catch { /* Browser may not expose long tasks. */ }
    }
    window.__uiPerf = state;
    requestAnimationFrame(countFrame);
  });

  await page.getByRole("button", { name: /Tìm tuyến & tạo lời giải thích/i }).click();
  await expect(page.getByRole("button", { name: /Tạm dừng mô phỏng/i })).toBeVisible();
  await page.waitForTimeout(3_500);
  const metrics = await page.evaluate(() => {
    const state = window.__uiPerf!;
    state.observer?.disconnect();
    const durations = state.longTasks;
    return {
      frames: state.frames,
      longTaskCount: durations.length,
      longTaskTotalMs: durations.reduce((sum, value) => sum + value, 0),
      longestTaskMs: Math.max(0, ...durations),
      domNodes: document.getElementsByTagName("*").length,
      svgPaths: document.querySelectorAll("svg path").length,
      traceIndex: Number((document.querySelector('.playback input[type="range"]') as HTMLInputElement)?.value || 0),
    };
  });
  console.log(`UI_PERF ${JSON.stringify(metrics)}`);

  expect(metrics.traceIndex).toBeGreaterThan(30);
  expect(metrics.frames).toBeGreaterThan(120);
  expect(metrics.longestTaskMs).toBeLessThan(250);
  expect(metrics.longTaskTotalMs).toBeLessThan(650);
  expect(metrics.domNodes).toBeLessThan(2_200);
  expect(metrics.svgPaths).toBeLessThan(450);
  expect(graphRequests).toBe(1);
});

test("traffic scenario updates do not lock the main thread", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".leaflet-map")).toBeVisible();
  await page.evaluate(() => {
    const state = { frames: 0, longTasks: [] as number[], startedAt: performance.now(), observer: undefined as PerformanceObserver | undefined };
    const countFrame = () => {
      state.frames += 1;
      if (performance.now() - state.startedAt < 2_500) requestAnimationFrame(countFrame);
    };
    state.observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) state.longTasks.push(entry.duration);
    });
    try { state.observer.observe({ entryTypes: ["longtask"] }); } catch { /* Optional API. */ }
    window.__uiPerf = state;
    requestAnimationFrame(countFrame);
  });

  const startedAt = Date.now();
  const scenarioSelect = page.locator('select:has(option[value="heavy_rain"])');
  await scenarioSelect.selectOption("heavy_rain");
  await expect(scenarioSelect).toHaveValue("heavy_rain");
  await expect(page.locator(".header-signals")).toContainText("Heavy rain");
  await expect(page.locator(".map-loading")).toBeHidden();
  const interactionMs = Date.now() - startedAt;
  await page.waitForTimeout(1_000);
  const metrics = await page.evaluate(() => {
    const state = window.__uiPerf!;
    state.observer?.disconnect();
    return {
      frames: state.frames,
      longTaskCount: state.longTasks.length,
      longTaskTotalMs: state.longTasks.reduce((sum, value) => sum + value, 0),
      longestTaskMs: Math.max(0, ...state.longTasks),
    };
  });
  console.log(`SCENARIO_PERF ${JSON.stringify({ ...metrics, interactionMs })}`);
  expect(interactionMs).toBeLessThan(2_500);
  expect(metrics.longestTaskMs).toBeLessThan(250);
});

test("map pan remains fluid with all roads and nodes rendered", async ({ page }) => {
  await page.goto("/");
  const map = page.locator(".leaflet-map");
  await expect(map).toBeVisible();
  const box = await map.boundingBox();
  if (!box) throw new Error("Map bounds unavailable");
  await page.evaluate(() => {
    const state = { frames: 0, longTasks: [] as number[], startedAt: performance.now(), observer: undefined as PerformanceObserver | undefined };
    const countFrame = () => {
      state.frames += 1;
      if (performance.now() - state.startedAt < 2_000) requestAnimationFrame(countFrame);
    };
    state.observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) state.longTasks.push(entry.duration);
    });
    try { state.observer.observe({ entryTypes: ["longtask"] }); } catch { /* Optional API. */ }
    window.__uiPerf = state;
    requestAnimationFrame(countFrame);
  });

  const centerX = box.x + box.width * 0.55;
  const centerY = box.y + box.height * 0.55;
  await page.mouse.move(centerX, centerY);
  await page.mouse.down();
  await page.mouse.move(centerX - 180, centerY + 60, { steps: 35 });
  await page.mouse.move(centerX + 120, centerY - 45, { steps: 35 });
  await page.mouse.up();
  await page.waitForTimeout(500);
  const metrics = await page.evaluate(() => {
    const state = window.__uiPerf!;
    state.observer?.disconnect();
    return {
      frames: state.frames,
      longTaskCount: state.longTasks.length,
      longTaskTotalMs: state.longTasks.reduce((sum, value) => sum + value, 0),
      longestTaskMs: Math.max(0, ...state.longTasks),
    };
  });
  console.log(`PAN_PERF ${JSON.stringify(metrics)}`);
  expect(metrics.frames).toBeGreaterThan(60);
  expect(metrics.longestTaskMs).toBeLessThan(250);
});

test("late-stage playback remains responsive with a large search tree", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Tìm tuyến & tạo lời giải thích/i }).click();
  await expect(page.getByRole("button", { name: /Tạm dừng mô phỏng/i })).toBeVisible();
  await page.getByRole("button", { name: /Tạm dừng mô phỏng/i }).click();
  const timeline = page.getByLabel("Tiến trình mô phỏng thuật toán");
  await timeline.evaluate((element: HTMLInputElement) => {
    element.value = String(Math.max(1, Number(element.max) - 35));
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await expect(timeline).not.toHaveValue("0");
  await page.evaluate(() => {
    const state = { frames: 0, longTasks: [] as number[], startedAt: performance.now(), observer: undefined as PerformanceObserver | undefined };
    const countFrame = () => {
      state.frames += 1;
      if (performance.now() - state.startedAt < 2_000) requestAnimationFrame(countFrame);
    };
    state.observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) state.longTasks.push(entry.duration);
    });
    try { state.observer.observe({ entryTypes: ["longtask"] }); } catch { /* Optional API. */ }
    window.__uiPerf = state;
    requestAnimationFrame(countFrame);
  });
  await page.getByRole("button", { name: /Phát mô phỏng/i }).click();
  await page.waitForTimeout(2_000);
  const metrics = await page.evaluate(() => {
    const state = window.__uiPerf!;
    state.observer?.disconnect();
    return {
      frames: state.frames,
      longTaskCount: state.longTasks.length,
      longTaskTotalMs: state.longTasks.reduce((sum, value) => sum + value, 0),
      longestTaskMs: Math.max(0, ...state.longTasks),
      svgPaths: document.querySelectorAll("svg path").length,
    };
  });
  console.log(`LATE_TRACE_PERF ${JSON.stringify(metrics)}`);
  expect(metrics.frames).toBeGreaterThan(80);
  expect(metrics.longestTaskMs).toBeLessThan(250);
  expect(metrics.svgPaths).toBeLessThan(450);
});
