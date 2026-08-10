import { expect, test } from "@playwright/test";

test("route simulation shows a semantic search tree without internal debug text", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Mạng lưới giao nhận/i })).toBeVisible();
  await expect(page.locator(".leaflet-map")).toBeVisible();

  await page.getByRole("button", { name: /Tìm tuyến & tạo lời giải thích/i }).click();
  await expect(page.locator(".search-hud")).toBeVisible();
  await expect(page.getByRole("button", { name: /Tạm dừng mô phỏng/i })).toBeVisible();

  await page.waitForTimeout(700);
  await page.getByRole("button", { name: /Tạm dừng mô phỏng/i }).click();
  await expect(page.locator(".search-tree-explored")).toHaveCount(1);
  await expect(page.locator(".search-tree-frontier")).toHaveCount(1);
  await expect(page.locator(".search-edge-active")).toHaveCount(1);
  await expect(page.locator(".trace-stats")).toContainText("đã mở rộng");

  const timeline = page.getByLabel("Tiến trình mô phỏng thuật toán");
  const beforeStep = Number(await timeline.inputValue());
  expect(beforeStep).toBeGreaterThan(3);
  await page.getByRole("button", { name: /Tiến một bước mở rộng/i }).click();
  await expect(timeline).toHaveValue(String(beforeStep + 1));
  await page.screenshot({ path: "test-results/polished-search.png", fullPage: true });

  const uiText = await page.locator("body").innerText();
  expect(uiText).not.toMatch(/osm_path_|osm_\d+|parent_id|edge_id|node_id|travel_time|morning_rush|\bdebug\b/i);

  await page.getByRole("button", { name: /Đi tới kết quả cuối/i }).click();
  await expect(page.locator(".search-hud")).toContainText("Đã dựng tuyến");
  await expect(page.locator(".final-route")).toHaveCount(1);
  await page.screenshot({ path: "test-results/polished-route.png", fullPage: true });

  const goalSelect = page.locator(".location-field select").nth(1);
  const currentGoal = await goalSelect.inputValue();
  const replacementGoal = await goalSelect.locator("option").evaluateAll((options, selected) =>
    (options as HTMLOptionElement[]).find((option) => option.value && option.value !== selected)?.value || "", currentGoal);
  expect(replacementGoal).not.toBe("");
  await goalSelect.selectOption(replacementGoal);
  await expect(page.locator(".status-pill.idle")).toContainText("Chờ chạy");
  await expect(page.locator(".final-route")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Phát mô phỏng/i })).toBeDisabled();
});

test("mobile layout avoids horizontal overflow and keeps playback operable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.locator(".map-frame")).toBeVisible();
  const sizes = await page.evaluate(() => ({ viewport: window.innerWidth, document: document.documentElement.scrollWidth }));
  expect(sizes.document).toBeLessThanOrEqual(sizes.viewport + 1);
  await expect(page.getByRole("button", { name: /Phát mô phỏng/i })).toBeDisabled();
  await expect(page.getByLabel("Tốc độ mô phỏng")).toBeVisible();
  await page.screenshot({ path: "test-results/polished-mobile.png", fullPage: true });
});
