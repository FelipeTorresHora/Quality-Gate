import { expect, test } from "@playwright/test";

test("GitHub login starts from production and preserves callback origin", async ({
  page,
  request,
  baseURL
}) => {
  const authMe = await request.get("/server/api/auth/me");
  expect(authMe.status()).toBe(401);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in to review Pull Requests" }))
    .toBeVisible();
  await expect(page.getByText("Authentication is required.")).toHaveCount(0);

  await page.getByRole("link", { name: "Sign in with GitHub" }).click();
  await page.waitForURL(/github\.com\/login/);

  const githubUrl = new URL(page.url());
  expect(githubUrl.hostname).toBe("github.com");
  const authorizeUrl = githubUrl.pathname.includes("/login/oauth/authorize")
    ? githubUrl
    : new URL(githubUrl.searchParams.get("return_to") ?? "", githubUrl.origin);

  expect(authorizeUrl.pathname).toBe("/login/oauth/authorize");
  expect(authorizeUrl.searchParams.get("client_id")).toBeTruthy();
  expect(authorizeUrl.searchParams.get("state")).toBeTruthy();
  expect(authorizeUrl.searchParams.get("redirect_uri")).toBe(
    `${baseURL}/server/api/auth/github/callback`
  );
});
