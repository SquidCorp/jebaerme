import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NewJob } from "@/app/new/job/new-job";
import NewJobPage from "@/app/new/job/page";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("NewJob", () => {
  it("renders the page header", () => {
    render(<NewJobPage />);
    expect(
      screen.getByRole("heading", { name: "Add a new job description" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Paste a link to a job ad and get a clean markdown version",
      ),
    ).toBeInTheDocument();
  });

  it("shows firecrawl markdown after a successful submit", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        job_title: "Engineer",
        company_name: "Acme",
        markdown: "# Engineer\n\nAcme",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<NewJob />);
    await user.type(
      screen.getByLabelText("Ad URL"),
      "https://jobs.example.com/ad",
    );
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/jobs/new/url",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ad_url: "https://jobs.example.com/ad" }),
      }),
    );
    expect(await screen.findByText(/# Engineer/)).toBeInTheDocument();
    expect(screen.getByText(/Acme/)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("job_title");
  });

  it("shows a gateway error and omits the result", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(502, { error: "upstream_error" })),
    );

    render(<NewJob />);
    await user.type(
      screen.getByLabelText("Ad URL"),
      "https://jobs.example.com/ad",
    );
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("upstream_error")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("job_title");
  });
});
