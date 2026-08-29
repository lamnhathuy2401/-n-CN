export function riskClass(level?: string | null): string {
  if (level === "high") return "badge badge-high";
  if (level === "medium") return "badge badge-medium";
  return "badge badge-low";
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    submitted: "Đã nộp",
    analyzing: "Đang phân tích",
    pending_review: "Chờ kiểm duyệt",
    approved: "Đã chấp nhận",
    flagged: "Đánh dấu nghi ngờ",
    needs_clarification: "Cần làm rõ",
  };
  return map[status] || status;
}

export function formatPct(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}
