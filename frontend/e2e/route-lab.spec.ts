import { expect, test } from "@playwright/test";

test("loads the real graph, runs A*, plays trace, and compares algorithms", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") pageErrors.push(message.text());
  });

  if (process.env.CAPTURE_DOCS === "1") {
    await page.setViewportSize({ width: 1720, height: 1450 });
    await page.emulateMedia({ reducedMotion: "reduce" });
  }

  await page.goto("/");
  if (process.env.CAPTURE_DOCS === "1") {
    await page.addStyleTag({ content: ".panel { backdrop-filter: none !important; } .leaflet-tile-pane { display: none !important; }" });
  }
  await expect(page.getByText("Engine online")).toBeVisible();
  await expect(page.getByText(/1103 nút • 2279 cung/)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Mạng lưới giao nhận trung tâm Thành phố Hồ Chí Minh/ })).toBeVisible();
  if (process.env.CAPTURE_DOCS === "1") {
    await page.waitForTimeout(800);
    await page.screenshot({ path: "../docs/assets/dashboard-overview.png", fullPage: true });
  }

  await page.getByRole("button", { name: /Tìm tuyến & tạo lời giải thích/ }).click();
  await expect(page.locator(".status-pill.success").getByText("Đã tìm thấy tuyến", { exact: true })).toBeVisible();
  await expect(page.getByText("Vì sao chọn tuyến này?")).toBeVisible();
  await expect(page.locator(".path-scroll > span").first()).toBeVisible();
  await expect(page.locator(".metric-card strong").first()).not.toHaveText("—");
  await expect(page.locator(".playback input[type=range]")).toBeEnabled();
  await expect(page.locator(".breakdown-row")).toHaveCount(4);
  if (process.env.CAPTURE_DOCS === "1") {
    await page.waitForTimeout(900);
    await page.screenshot({ path: "../docs/assets/route-result.png", fullPage: true });
  }

  await page.getByRole("button", { name: "So sánh" }).click();
  await expect(page.getByRole("heading", { name: "Algorithm arena" })).toBeVisible();
  await page.getByRole("button", { name: /Chạy benchmark 4 thuật toán/ }).click();
  await expect(page.locator(".winner-card")).toBeVisible();
  await expect(page.locator(".benchmark-table tbody tr")).toHaveCount(4);
  if (process.env.CAPTURE_DOCS === "1") {
    await page.waitForTimeout(400);
    await page.screenshot({ path: "../docs/assets/algorithm-compare.png", fullPage: true });

    await page.getByRole("button", { name: "Nhiều điểm" }).click();
    const stopPicker = page.getByLabel("Thêm điểm giao");
    await stopPicker.selectOption({ index: 1 });
    await stopPicker.selectOption({ index: 1 });
    await page.getByRole("button", { name: "Tối ưu hành trình" }).click();
    await expect(page.locator(".status-pill.success")).toContainText("Đã tìm thấy tuyến");
    await expect(page.locator(".delivery-leg").first()).toBeVisible();
    await page.waitForTimeout(400);
    await page.screenshot({ path: "../docs/assets/multi-stop.png", fullPage: true });

    await page.getByRole("button", { name: "Tìm tuyến" }).click();
    const scenarioSelect = page.locator('select:has(option[value="heavy_rain"])');
    await scenarioSelect.selectOption("heavy_rain");
    await expect(page.locator(".map-loading")).toBeHidden();
    await page.getByRole("button", { name: /Tìm tuyến & tạo lời giải thích/ }).click();
    await expect(page.locator(".status-pill.success")).toContainText("Đã tìm thấy tuyến");
    await page.waitForTimeout(900);
    await page.screenshot({ path: "../docs/assets/heavy-rain.png", fullPage: true });

    await page.getByRole("button", { name: "Thuật toán" }).click();
    await expect(page.getByRole("heading", { name: /Search algorithms/ })).toBeVisible();
    await page.waitForTimeout(900);
    await page.screenshot({ path: "../docs/assets/algorithm-learn.png", fullPage: true });
  }

  expect(pageErrors).toEqual([]);
});

test("multi-stop planner preserves optimized legs in the UI", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/1103 nút • 2279 cung/)).toBeVisible();
  await page.getByRole("button", { name: "Nhiều điểm" }).click();
  const stopPicker = page.getByLabel("Thêm điểm giao");
  await stopPicker.selectOption({ index: 1 });
  await stopPicker.selectOption({ index: 1 });
  await expect(page.locator(".stop-chip")).toHaveCount(2);
  await page.getByRole("button", { name: "Tối ưu hành trình" }).click();
  await expect(page.locator(".status-pill.success")).toContainText("Đã tìm thấy tuyến");
  await expect(page.locator(".delivery-leg")).toHaveCount(2);
  await expect(page.locator(".path-scroll > span")).toHaveCount(3);
});

test("theory deck and mobile layout remain usable", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 900 });
  await page.goto("/");
  await page.getByRole("button", { name: "Thuật toán" }).click();
  await expect(page.getByRole("heading", { name: /Search algorithms/ })).toBeVisible();
  await expect(page.locator(".algorithm-card")).toHaveCount(8);
  await expect(page.locator(".heuristic-list > div")).toHaveCount(4);
  const hasPageOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(hasPageOverflow).toBe(false);
});
