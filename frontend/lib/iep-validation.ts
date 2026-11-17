export interface SmartGoalFields {
  title?: unknown;
  goalArea?: unknown;
  targetTimeframe?: unknown;
  measurementMethod?: unknown;
  rationale?: unknown;
  milestones?: unknown;
}

/**
 * Deterministic completeness prompts for therapist review. This deliberately
 * reports missing detail instead of assigning clinical quality or blocking an
 * IEP: appropriateness and achievability require professional judgment.
 */
export function smartCompletenessWarnings(goal: SmartGoalFields): string[] {
  const warnings: string[] = [];
  const title = typeof goal.title === "string" ? goal.title.trim() : "";
  const titleWords = title.split(/\s+/).filter(Boolean);
  const measurement = typeof goal.measurementMethod === "string" ? goal.measurementMethod.trim() : "";
  const timeframe = typeof goal.targetTimeframe === "string" ? goal.targetTimeframe.trim() : "";
  const rationale = typeof goal.rationale === "string" ? goal.rationale.trim() : "";

  if (titleWords.length < 8) warnings.push("Specific: describe one observable learner action and its setting.");
  if (!/\d|%|\b(times|opportunities|sessions|minutes|seconds|days|weeks)\b/i.test(`${title} ${measurement}`)) {
    warnings.push("Measurable: add a count, frequency, duration, percentage, or other observable criterion.");
  }
  if (typeof goal.goalArea !== "string" || !goal.goalArea.trim() || !rationale) {
    warnings.push("Relevant: select a goal area and explain how the goal relates to the learner's needs.");
  }
  if (!timeframe && !hasDatedMilestone(goal.milestones)) {
    warnings.push("Time-bound: add a target timeframe or a dated milestone.");
  }

  return warnings;
}

function hasDatedMilestone(value: unknown): boolean {
  if (!Array.isArray(value)) return false;
  return value.some((milestone) => {
    if (!milestone || typeof milestone !== "object") return false;
    const targetDate = (milestone as { targetDate?: unknown }).targetDate;
    return typeof targetDate === "string" && targetDate.trim().length > 0;
  });
}
