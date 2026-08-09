import { describe, expect, it } from "vitest";

import { nodeKeywords } from "./nodeKeywords";

/** A node fixture shaped like the real `data/processed/graph.json` entries
 *  (osm_node_id number, road_names string[], raw_degree number) — the same
 *  shape that prompted F1 in the latest review. */
const REAL_NODE = {
  kind: "intersection",
  attributes: {
    osm_node_id: 366367996,
    road_names: ["Trường Sa", "Đặng Văn Ngữ"],
    raw_degree: 3,
  },
};

describe("nodeKeywords (T18)", () => {
  it("includes string[] attributes such as road_names verbatim", () => {
    const blob = nodeKeywords(REAL_NODE);
    expect(blob).toContain("Trường Sa");
    expect(blob).toContain("Đặng Văn Ngữ");
  });

  it("still joins the node kind so kind-based queries still hit", () => {
    const blob = nodeKeywords(REAL_NODE);
    expect(blob).toContain("intersection");
  });

  it("ignores non-string attribute values (numbers, objects) without throwing", () => {
    const blob = nodeKeywords({
      kind: "delivery_supermarket",
      attributes: { count: 7, owner: { id: "x" } } as unknown as Record<string, unknown>,
    });
    expect(blob).toBe("delivery_supermarket");
  });

  it("falls back to a kind-only blob when attributes are missing", () => {
    const blob = nodeKeywords({ kind: "gateway" });
    expect(blob).toBe("gateway");
  });

  it("concatenates a mix of flat strings and string[] entries", () => {
    const blob = nodeKeywords({
      kind: "delivery_hospital",
      attributes: {
        road_names: ["Nguyễn Tri Phuong"],
        ward: "District 5",
      },
    });
    expect(blob).toContain("Nguyễn Tri Phuong");
    expect(blob).toContain("District 5");
    expect(blob).toContain("delivery_hospital");
  });
});
