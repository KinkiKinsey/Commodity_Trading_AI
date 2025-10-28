/**
 * Capture Bloomberg quote page sections via existing Chrome instance.
 * Launch Chrome with remote debugging, pass captcha manually, then run this script.
 */

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const CDP_ENDPOINT = "http://127.0.0.1:9222";
const TARGET_URL = "https://www.bloomberg.com/quote/SPX:IND";
const ROOT_DIR = __dirname;
const OUTPUT_DIR = path.join(ROOT_DIR, "screenshots");
const META_DIR = path.join(ROOT_DIR, "metadata");

const SHOTS = [
  { name: "nav-top.png", selectors: [".nav_nav__7WSAd"] },
  { name: "hero-overview.png", selectors: ["[data-component=\"quote-header\"]", "[data-component=\"quote-hero\"]", ".quote-header__container"] },
  { name: "chart-tools.png", selectors: ["[data-component=\"chart-toolbar\"]", ".quote-chart-toolbar"] },
  { name: "chart-area.png", selectors: ["[data-component=\"interactive-chart\"]", ".interactive-chart__container"] },
  { name: "news-top-stories.png", selectors: ["[data-component=\"top-stories\"]", ".top-stories-module"] },
  { name: "news-latest.png", selectors: ["[data-component=\"latest-news\"]", ".latest-news-module"] },
  { name: "right-rail.png", selectors: ["[data-component=\"quote-right-rail\"]", ".quote-sidebar__container"] },
  { name: "footer-ticker.png", selectors: ["footer", ".quote-footer"] }
];

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function waitForEnter(message) {
  return new Promise((resolve) => {
    process.stdout.write(message);
    process.stdin.once("data", () => resolve());
  });
}

async function extractMetadata(page) {
  return page.evaluate(() => {
    const summary = {};

    const nav = document.querySelector(".nav_nav__7WSAd");
    if (nav) {
      summary.navigation = {
        textSample: nav.innerText.slice(0, 300),
        items: Array.from(nav.querySelectorAll("a.nav_quoteNavLink__kQ4sS")).map((a) => ({
          label: a.textContent.trim(),
          href: a.href
        }))
      };
    }

    const hero = document.querySelector("[data-component=\"quote-header\"]");
    if (hero) {
      summary.hero = {
        price: hero.querySelector("[data-component=\"price\"]")?.textContent.trim() ?? null,
        change: hero.querySelector("[data-component=\"change\"]")?.textContent.trim() ?? null,
        actions: Array.from(hero.querySelectorAll("button, a")).slice(0, 5).map((btn) => ({
          text: btn.textContent.trim(),
          tag: btn.tagName,
          href: btn.href ?? null
        }))
      };
    }

    const toolbar = document.querySelector("[data-component=\"chart-toolbar\"]");
    if (toolbar) {
      summary.chartToolbar = Array.from(toolbar.querySelectorAll("button, li, a")).map((el) => ({
        text: el.textContent.trim(),
        tag: el.tagName
      }));
    }

    const topStories = document.querySelector("[data-component=\"top-stories\"]");
    if (topStories) {
      summary.topStories = Array.from(topStories.querySelectorAll("article")).slice(0, 3).map((article) => ({
        headline: article.querySelector("h3, h2")?.textContent.trim() ?? "",
        source: article.querySelector("span")?.textContent.trim() ?? ""
      }));
    }

    const latestNews = document.querySelector("[data-component=\"latest-news\"]");
    if (latestNews) {
      summary.latestNews = Array.from(latestNews.querySelectorAll("li")).slice(0, 5).map((item) => ({
        title: item.querySelector("a")?.textContent.trim() ?? "",
        time: item.querySelector("time")?.textContent.trim() ?? ""
      }));
    }

    const rightRail = document.querySelector("[data-component=\"quote-right-rail\"]");
    if (rightRail) {
      summary.rightRailSections = Array.from(rightRail.querySelectorAll("section")).map((section) => ({
        title: section.querySelector("h3, h2")?.textContent.trim() ?? "",
        items: Array.from(section.querySelectorAll("li, p")).slice(0, 5).map((n) => n.textContent.trim())
      }));
    }

    return summary;
  });
}

async function getActivePage(context, currentPage) {
  if (currentPage && !currentPage.isClosed()) return currentPage;
  const pages = context.pages();
  if (pages.length === 0) throw new Error("No available page in context");
  return pages[pages.length - 1];
}

async function captureSection(page, shot) {
  let element = null;
  for (const selector of shot.selectors) {
    element = await page.$(selector);
    if (element) break;
  }
  if (!element) {
    console.warn(`⚠️  Selectors not found, skipping ${shot.name}: ${shot.selectors.join(", ")}`);
    return;
  }
  const outputPath = path.join(OUTPUT_DIR, shot.name);
  await element.scrollIntoViewIfNeeded();
  await element.waitForElementState?.("visible");
  await element.screenshot({ path: outputPath });
  console.log(`✔ Screenshot saved: ${outputPath}`);
}

async function main() {
  ensureDir(OUTPUT_DIR);
  ensureDir(META_DIR);

  const browser = await chromium.connectOverCDP(CDP_ENDPOINT);
  let [context] = browser.contexts();
  if (!context) context = await browser.newContext();

  let [page] = context.pages();
  if (!page) page = await context.newPage();

  context.on("page", (newPage) => {
    page = newPage;
  });

  if (!page.url().includes("/quote/")) {
    console.log(`Navigating to ${TARGET_URL}`);
    await page.goto(TARGET_URL, { waitUntil: "domcontentloaded" });
  } else {
    await page.bringToFront();
  }

  console.log("\n确认目标页面已通过验证并保持打开。");
  await waitForEnter("准备好后按 Enter 开始捕获…");

  const metadata = {};
  for (const shot of SHOTS) {
    try {
      page = await getActivePage(context, page);
      await captureSection(page, shot);
    } catch (error) {
      console.warn(`⚠️  捕获 ${shot.name} 失败：${error.message}`);
    }
  }

  try {
    page = await getActivePage(context, page);
    Object.assign(metadata, await extractMetadata(page));
    const components = await page.evaluate(() =>
      Array.from(new Set(Array.from(document.querySelectorAll("[data-component]")).map((el) => el.getAttribute("data-component"))))
    );
    metadata.availableComponents = components;
    metadata.savedAt = new Date().toISOString();
    const htmlPath = path.join(META_DIR, "page_dump.html");
    fs.writeFileSync(htmlPath, await page.content(), { encoding: "utf8" });
    const metaPath = path.join(META_DIR, "layout.json");
    fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2), { encoding: "utf8" });
    console.log(`✔ 元数据写入：${metaPath}`);
    console.log(`✔ 页面 HTML 保存：${htmlPath}`);
  } catch (error) {
    console.warn(`⚠️  导出元数据失败：${error.message}`);
  }

  console.log("完成。如需再次捕获，保持浏览器打开并重跑脚本。");
  process.exit(0);
}

main().catch((error) => {
  console.error("脚本执行失败：", error);
  process.exit(1);
});
