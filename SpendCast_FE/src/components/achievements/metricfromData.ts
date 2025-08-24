import coffeeData from '../../../../data-extraction/output/coffee_spend.json';
import foodData from '../../../../data-extraction/output/healthy_spend.json';
import transportData from '../../../../data-extraction/output/transport_spend.json';
import swissData from '../../../../data-extraction/output/swiss_made_spend.json';
import mediaData from '../../../../data-extraction/output/media_subscriptions_spend.json';
import alcoholData from '../../../../data-extraction/output/alcohol_spend.json';
import type { Metrics, SpendRow } from './type';

// --- helpers ---
const parseChf = (s?: string) =>
  s ? parseFloat(s.replace('CHF', '').trim()) : 0;

const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);

function sumAmount(
  rows: SpendRow[],
  isoMonth: string,
  predicate?: (r: SpendRow) => boolean
): number {
  const filtered = rows.filter(
    (r) => r.monthISO === isoMonth && (!predicate || predicate(r))
  );
  return sum(filtered.map((r) => parseChf(r.amount)));
}

// --- main builder ---
// Prefer passing isoMonth in from the page; fallback to the current month.
export function buildMetrics(isoMonth?: string): Metrics {
  const month = "2024-07";

  // Coffee
  const coffeeSpend = sumAmount(coffeeData as SpendRow[], month, (r) => r.category === 'coffee');

  // Food
  const healthyFoodSpend = sumAmount(foodData as SpendRow[], month, (r) => r.category === 'healthy');
  const unhealthyFoodSpend = sumAmount(foodData as SpendRow[], month, (r) => r.category === 'unhealthy');

  // Transport
  const publictransportSpend = sumAmount(transportData as SpendRow[], month, (r) => r.category === 'public transport');
  const fuelSpend = sumAmount(transportData as SpendRow[], month, (r) => r.category === 'fuel');
  // total transport = sum all categories for the month
  const transportSpend = sumAmount(transportData as SpendRow[], month);

  // Swiss-made item counts
  const swissMadeSpend = sumAmount(swissData as SpendRow[], month, (r) => r.category === 'Swiss-made');
  const nonswissMadeSpend = sumAmount(swissData as SpendRow[], month, (r) => r.category === 'not Swiss-made');

  // Media subscriptions (looks like a count file, not CHF)
  const mediaSubscription = sumAmount(mediaData as SpendRow[], month);

  // Alcohol
  const alcoholSpend = sumAmount(alcoholData as SpendRow[], month, (r) => r.category === 'alcohol' || r.category === 'beer' || r.category === 'wine' || r.category === 'spirits');

  // You can compute this from item data if you have it; placeholder for now
  const totalSpend= swissMadeSpend + nonswissMadeSpend;

  return {
    coffeeSpend,
    healthyFoodSpend,
    unhealthyFoodSpend,
    publictransportSpend,
    fuelSpend,
    transportSpend,
    swissMadeSpend,
    nonswissMadeSpend,
    mediaSubscription,
    totalSpend,
    alcoholSpend,
    alcoholMonthlyLimit: 100,      // tune or fetch from user settings
    consecutiveMonthsUnderBudget: 2, // compute if you track history
  };
}
