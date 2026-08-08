import { expect, test } from "@playwright/test";

test("loads the real graph, runs A*, plays trace, and compares algorithms", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") pageErrors.push(message.text());
  });

  await page.goto("/");
  await expect(page.getByText("Engine online")).toBeVisible();
  await expect(page.getByText(/512 nút • 1007 cung/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Mạng lưới cấp cứu trung tâm Đà Nẵng" })).toBeVisible();

  await page.getByRole("button", { name: /Tìm tuyến & tạo lời giải thích/ }).click();
  await expect(page.locator(".status-pill.success").getByText("Route found", { exact: true })).toBeVisible();
  await expect(page.getByText("Vì sao chọn tuyến này?")).toBeVisible();
  await expect(page.locator(".path-scroll > span").first()).toBeVisible();
  await expect(page.locator(".metric-card strong").first()).not.toHaveText("—");
  await expect(page.locator(".playback input[type=range]")).toBeEnabled();
  await expect(page.locator(".breakdown-row")).toHaveCount(4);
  if (process.env.CAPTURE_DOCS === "1") {
    await page.screenshot({ path: "../docs/assets/route-result.png", fullPage: true });
  }

  await page.getByRole("button", { name: "So sánh" }).click();
  await expect(page.getByRole("heading", { name: "Algorithm arena" })).toBeVisible();
  await page.getByRole("button", { name: /Chạy benchmark 4 thuật toán/ }).click();
  await expect(page.locator(".winner-card")).toBeVisible();
  await expect(page.locator(".benchmark-table tbody tr")).toHaveCount(4);
  if (process.env.CAPTURE_DOCS === "1") {
    await page.screenshot({ path: "../docs/assets/algorithm-compare.png", fullPage: true });
  }

  expect(pageErrors).toEqual([]);
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
