import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NewKnowledge } from "@/app/new/knowledge/new-knowledge";
import NewKnowledgePage from "@/app/new/knowledge/page";

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

const successBody = {
  document_id: "doc-1",
  chunk_count: 1,
  skipped_chunks: 0,
  title: "cv",
  source: "cv",
  domain: "general",
  source_priority: 50,
  point_ids: ["p1"],
};

const defaultBody = {
  title: "cv",
  text: "hello knowledge",
  source: "cv",
  source_kind: "file",
  domain: "general",
  language: "en",
  roles: [] as string[],
  source_ids: ["cv.md"],
};

function cvFile(): File {
  return new File(["hello knowledge"], "cv.md", { type: "text/markdown" });
}

function stubFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(jsonResponse(status, body));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function uploadCvAndSelectSource() {
  const user = userEvent.setup();
  await user.upload(screen.getByLabelText("File"), cvFile());
  await user.selectOptions(screen.getByLabelText("Source"), "cv");
  return user;
}

describe("NewKnowledge page", () => {
  it("renders the page header", () => {
    render(<NewKnowledgePage />);
    expect(
      screen.getByRole("heading", { name: "Add knowledge" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Upload a markdown or text file into the document store",
      ),
    ).toBeInTheDocument();
  });
});

describe("NewKnowledge submit", () => {
  it("submits a markdown file with defaults", async () => {
    const fetchMock = stubFetch(200, successBody);
    render(<NewKnowledge />);
    const user = await uploadCvAndSelectSource();
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/documents",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(defaultBody),
      }),
    );
    expect(await screen.findByText(/document_id: doc-1/)).toBeInTheDocument();
    expect(screen.getByText(/chunk_count: 1/)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("point_ids");
  });

  it("submits edited title domain and roles", async () => {
    const fetchMock = stubFetch(200, successBody);
    render(<NewKnowledge />);
    const user = await uploadCvAndSelectSource();
    const titleInput = screen.getByLabelText("Title");
    await user.clear(titleInput);
    await user.type(titleInput, "Resume");
    await user.selectOptions(screen.getByLabelText("Domain"), "technical");
    await user.type(
      screen.getByLabelText("Roles"),
      "Staff Engineer, Tech Lead",
    );
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/documents",
      expect.objectContaining({
        body: JSON.stringify({
          ...defaultBody,
          title: "Resume",
          domain: "technical",
          roles: ["Staff Engineer", "Tech Lead"],
        }),
      }),
    );
  });
});

describe("NewKnowledge errors", () => {
  it("rejects a non-text file", () => {
    const fetchMock = stubFetch(200, successBody);
    render(<NewKnowledge />);
    fireEvent.change(screen.getByLabelText("File"), {
      target: {
        files: [new File(["%PDF"], "notes.pdf", { type: "application/pdf" })],
      },
    });

    expect(screen.getByText("Choose a .md or .txt file")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows a gateway error and omits the result", async () => {
    stubFetch(502, { error: "upstream_error" });
    render(<NewKnowledge />);
    const user = await uploadCvAndSelectSource();
    await user.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("upstream_error")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("document_id");
  });
});
