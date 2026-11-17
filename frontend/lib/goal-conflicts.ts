import type { IEPGoal } from "@/types";

const DIRECTION_PAIRS: Array<[RegExp, RegExp]> = [
  [/\b(increase|improve|more|higher|longer|frequent)\b/i, /\b(decrease|reduce|less|lower|shorter|infrequent)\b/i],
  [/\bindependent(ly)?\b/i, /\bwith\s+(adult\s+)?prompts?\b/i],
  [/\binitiate\b/i, /\bavoid\b/i],
];
const STOP_WORDS = new Set("the a an to and or of in on with by for will can from during within across demonstrate use using student learner child goal increase improve more higher longer frequent independent independently initiate decrease reduce less lower shorter infrequent prompts prompt avoid".split(" "));

function opposingDirections(first: string, second: string) {
  return DIRECTION_PAIRS.some(([positive, negative]) =>
    (positive.test(first) && negative.test(second)) || (negative.test(first) && positive.test(second))
  );
}

function contentWords(title: string) {
  return new Set(title.toLowerCase().match(/[a-z]{3,}/g)?.filter((word) => !STOP_WORDS.has(word)) ?? []);
}

/**
 * Conservative, advisory-only check for goals that share a skill and ask for
 * opposing directions. It is a review prompt, not a clinical determination.
 */
export function findPossibleGoalConflicts(goals: Pick<IEPGoal, "title" | "goalArea">[]) {
  const conflicts: Array<{ first: number; second: number; sharedSkill: string }> = [];
  for (let first = 0; first < goals.length; first += 1) {
    for (let second = first + 1; second < goals.length; second += 1) {
      const left = goals[first];
      const right = goals[second];
      if ((left.goalArea || "General").trim().toLowerCase() !== (right.goalArea || "General").trim().toLowerCase()) continue;
      if (!opposingDirections(left.title, right.title)) continue;
      const rightWords = contentWords(right.title);
      const shared = [...contentWords(left.title)].filter((word) => rightWords.has(word));
      if (shared.length >= 2) conflicts.push({ first: first + 1, second: second + 1, sharedSkill: shared.slice(0, 3).join(", ") });
    }
  }
  return conflicts;
}
