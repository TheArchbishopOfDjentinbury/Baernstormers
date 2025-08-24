import coffeeData from '../../../../data-extraction/output/coffee_spend.json';
import foodData from '../../../../data-extraction/output/healthy_spend.json';
import transportData from '../../../../data-extraction/output/transport_spend.json';
import swissData from '../../../../data-extraction/output/swiss_made_spend.json';
import mediaData from '../../../../data-extraction/output/media_subscriptions_spend.json';
import alcoholData from '../../../../data-extraction/output/alcohol_spend.json';
import type { Metrics, SpendRow } from '@/components/Achievements/type';

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

export function buildMetrics(isoMonth?: string): Metrics {
  const month = isoMonth || new Date().toISOString().slice(0, 7); // Format: "2024-07"

  const coffeeSpend = sumAmount(
    coffeeData as SpendRow[],
    month,
    (r) => r.category === 'coffee'
  );

  const healthyFoodSpend = sumAmount(
    foodData as SpendRow[],
    month,
    (r) => r.category === 'healthy'
  );
  const unhealthyFoodSpend = sumAmount(
    foodData as SpendRow[],
    month,
    (r) => r.category === 'unhealthy'
  );

  const publictransportSpend = sumAmount(
    transportData as SpendRow[],
    month,
    (r) => r.category === 'public transport'
  );
  const fuelSpend = sumAmount(
    transportData as SpendRow[],
    month,
    (r) => r.category === 'fuel'
  );
  const transportSpend = sumAmount(transportData as SpendRow[], month);

  const swissMadeSpend = sumAmount(
    swissData as SpendRow[],
    month,
    (r) => r.category === 'Swiss-made'
  );
  const nonswissMadeSpend = sumAmount(
    swissData as SpendRow[],
    month,
    (r) => r.category === 'not Swiss-made'
  );

  const mediaSubscription = sumAmount(mediaData as SpendRow[], month);

  const alcoholSpend = sumAmount(
    alcoholData as SpendRow[],
    month,
    (r) =>
      r.category === 'alcohol' ||
      r.category === 'beer' ||
      r.category === 'wine' ||
      r.category === 'spirits'
  );

  const totalSpend = swissMadeSpend + nonswissMadeSpend;

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
    alcoholMonthlyLimit: 100,
    consecutiveMonthsUnderBudget: 2,
  };
}
